#!/usr/bin/env python3
"""
Simple run script for the SIH Logistics Optimization Dashboard
"""
import sys
import os

def main():
    """Launch the dashboard with proper error handling"""
    print("🚢🚂 SIH Logistics Optimization Dashboard")
    print("=" * 50)
    
    try:
        # Import and run the app
        import app
        print("🚀 Starting dashboard at http://127.0.0.1:5006/")
        print("🔧 Press Ctrl+C to stop")
        # Launch via the module's run_server helper (reloader disabled inside)
        app.run_server(debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try: pip install -r requirements_dash.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()