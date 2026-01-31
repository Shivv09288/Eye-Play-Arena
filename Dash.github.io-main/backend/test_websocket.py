"""
Test script to verify WebSocket server connectivity
Run this to diagnose WebSocket connection issues
"""
import socket
import asyncio
import websockets
import time

def check_port_listening(host='localhost', port=8765):
    """Check if a port is listening"""
    print(f"\n[1/3] Checking if port {port} is listening...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"✅ Port {port} is OPEN and listening")
            return True
        else:
            print(f"❌ Port {port} is CLOSED or not accepting connections")
            print(f"   Error code: {result}")
            return False
    except Exception as e:
        print(f"❌ Error checking port: {e}")
        return False
    finally:
        sock.close()

async def test_websocket_connection(uri='ws://localhost:8765'):
    """Test WebSocket connection"""
    print(f"\n[2/3] Testing WebSocket connection to {uri}...")
    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            print(f"✅ WebSocket connection SUCCESSFUL")
            
            # Send a test message
            test_msg = '{"test": "hello"}'
            await websocket.send(test_msg)
            print(f"✅ Test message sent successfully")
            
            # Wait briefly to receive any response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                print(f"✅ Received response: {response}")
            except asyncio.TimeoutError:
                print(f"⚠️  No immediate response (server may not echo messages)")
            
            return True
    except Exception as e:
        print(f"❌ WebSocket connection FAILED: {e}")
        return False

def check_firewall():
    """Provide firewall checking advice"""
    print(f"\n[3/3] Firewall/Network Checklist:")
    print("   • Windows Defender Firewall: Check if Python is allowed")
    print("   • Run: netstat -ano | findstr :8765  (to see if port is bound)")
    print("   • Try: Restart the eye_websocket_server.py")
    print("   • Try: Disable firewall temporarily to test")

def main():
    print("\n" + "="*70)
    print("WebSocket Connection Diagnostic Test")
    print("="*70)
    
    # Test 1: Port listening
    if not check_port_listening():
        print("\n❌ Port is not listening. Make sure eye_websocket_server.py is running!")
        check_firewall()
        return False
    
    # Test 2: WebSocket connection
    try:
        result = asyncio.run(test_websocket_connection())
        if result:
            print("\n" + "="*70)
            print("✅ ALL TESTS PASSED - WebSocket connection is working!")
            print("="*70)
            return True
    except Exception as e:
        print(f"\n❌ Async test failed: {e}")
    
    check_firewall()
    return False

if __name__ == "__main__":
    main()
