"""
MongoDB backend server for storing user game history and high scores
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['dash_game']
users_collection = db['users']
scores_collection = db['scores']

@app.route('/api/user/login', methods=['POST'])
def user_login():
    """Login or register user and return their history"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        # Find or create user
        user = users_collection.find_one({'username': username})
        
        if not user:
            # Create new user
            user = {
                'username': username,
                'created_at': datetime.now(),
                'last_login': datetime.now(),
                'total_games': 0,
                'high_score': 0
            }
            users_collection.insert_one(user)
            user['_id'] = str(user['_id'])
        else:
            # Update last login
            users_collection.update_one(
                {'username': username},
                {'$set': {'last_login': datetime.now()}}
            )
            user['_id'] = str(user['_id'])
        
        # Get user's score history
        scores = list(scores_collection.find(
            {'username': username}
        ).sort('score', -1).limit(10))
        
        for score in scores:
            score['_id'] = str(score['_id'])
            score['date'] = score['date'].isoformat()
        
        return jsonify({
            'success': True,
            'user': {
                'username': user['username'],
                'total_games': user['total_games'],
                'high_score': user['high_score'],
                'last_login': user['last_login'].isoformat()
            },
            'score_history': scores
        })
    
    except Exception as e:
        print(f"Error in user_login: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/score/save', methods=['POST'])
def save_score():
    """Save a new score for a user"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        score = data.get('score', 0)
        game_type = data.get('game_type', 'dash_racer')  # dash_racer, target_shooter, western_shooter, memory_match
        lap_time = data.get('lap_time', '')
        additional_stats = data.get('stats', {})  # Extra game-specific stats
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        # Save score
        score_doc = {
            'username': username,
            'game_type': game_type,
            'score': score,
            'lap_time': lap_time,
            'stats': additional_stats,
            'date': datetime.now()
        }
        scores_collection.insert_one(score_doc)
        
        # Update user stats (now tracking per game)
        user = users_collection.find_one({'username': username})
        if user:
            total_games = user.get('total_games', 0) + 1
            
            # Track high scores per game
            game_stats = user.get('game_stats', {})
            if game_type not in game_stats:
                game_stats[game_type] = {'high_score': 0, 'games_played': 0}
            
            game_stats[game_type]['games_played'] += 1
            old_high = game_stats[game_type]['high_score']
            game_stats[game_type]['high_score'] = max(old_high, score)
            is_new_high = score > old_high
            
            # Overall high score
            high_score = max(user.get('high_score', 0), score)
            
            users_collection.update_one(
                {'username': username},
                {
                    '$set': {
                        'total_games': total_games,
                        'high_score': high_score,
                        'game_stats': game_stats
                    }
                }
            )
            
            return jsonify({
                'success': True,
                'total_games': total_games,
                'high_score': high_score,
                'game_high_score': game_stats[game_type]['high_score'],
                'is_new_high_score': is_new_high,
                'games_played_this_type': game_stats[game_type]['games_played']
            })
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error in save_score: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get top 10 high scores across all users"""
    try:
        game_type = request.args.get('game_type', None)  # Optional filter by game
        
        # Build match filter
        match_filter = {}
        if game_type:
            match_filter['game_type'] = game_type
        
        # Aggregate to get best score per user (optionally per game)
        pipeline = [
            {'$match': match_filter} if match_filter else {'$match': {}},
            {
                '$group': {
                    '_id': '$username',
                    'high_score': {'$max': '$score'},
                    'game_type': {'$first': '$game_type'},
                    'best_lap_time': {'$first': '$lap_time'}
                }
            },
            {'$sort': {'high_score': -1}},
            {'$limit': 10}
        ]
        
        leaderboard = list(scores_collection.aggregate(pipeline))
        
        for entry in leaderboard:
            entry['username'] = entry.pop('_id')
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard,
            'game_type': game_type
        })
    
    except Exception as e:
        print(f"Error in get_leaderboard: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/stats', methods=['GET'])
def get_user_stats():
    """Get detailed stats for a specific user"""
    try:
        username = request.args.get('username', '').strip()
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        user = users_collection.find_one({'username': username})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get score history for all games
        scores = list(scores_collection.find(
            {'username': username}
        ).sort('date', -1).limit(20))
        
        for score in scores:
            score['_id'] = str(score['_id'])
            score['date'] = score['date'].isoformat()
        
        user['_id'] = str(user['_id'])
        user['created_at'] = user['created_at'].isoformat()
        user['last_login'] = user['last_login'].isoformat()
        
        return jsonify({
            'success': True,
            'user': user,
            'recent_scores': scores
        })
    
    except Exception as e:
        print(f"Error in get_user_stats: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("="*60)
    print("🎮 Dash Game - MongoDB Backend Server")
    print("="*60)
    print(f"MongoDB URI: {MONGO_URI}")
    print("Starting Flask server on http://localhost:5000")
    print("="*60)
    app.run(debug=True, port=5000)
