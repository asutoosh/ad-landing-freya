"""
Launcher script to run both bot.py and worker.py simultaneously
"""
import subprocess
import sys
import os

def main():
    print("🚀 Starting Telegram Bot System...")
    print("=" * 50)
    
    # Start both processes
    try:
        bot_process = subprocess.Popen(
            [sys.executable, "bot.py"],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        print("✅ Bot process started (PID: {})".format(bot_process.pid))
        
        worker_process = subprocess.Popen(
            [sys.executable, "worker.py"],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        print("✅ Worker process started (PID: {})".format(worker_process.pid))
        
        print("=" * 50)
        print("🎉 Both processes are running!")
        print("Press Ctrl+C to stop both processes")
        print("=" * 50)
        
        # Wait for processes to complete
        bot_process.wait()
        worker_process.wait()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Stopping processes...")
        bot_process.terminate()
        worker_process.terminate()
        bot_process.wait()
        worker_process.wait()
        print("✅ Both processes stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
