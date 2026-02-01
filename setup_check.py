"""
Setup and validation script for Kalshi Trading Bot
Run this first to check your environment and configuration
"""
import sys
import os
from pathlib import Path


def check_python_version():
    """Verify Python 3.10+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10+ required")
        print(f"   Current: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if dependencies are installed"""
    required = ['aiohttp', 'pandas', 'python-dotenv', 'colorlog', 'backoff', 'aiolimiter']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - not installed")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Missing packages. Install with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    return True


def check_env_file():
    """Verify .env exists and has required keys"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found")
        print("   Copy .env.example to .env and add your API keys")
        return False
    
    print("✅ .env file exists")
    
    # Check for required keys
    required_keys = ['KALSHI_API_KEY', 'KALSHI_API_SECRET', 'KALSHI_ENV']
    with open(env_path) as f:
        content = f.read()
    
    missing_keys = []
    for key in required_keys:
        if f"{key}=" not in content or f"{key}=your_" in content or f"{key}=\n" in content:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"⚠️ Missing or incomplete keys in .env:")
        for key in missing_keys:
            print(f"   - {key}")
        return False
    
    print("✅ .env configured")
    return True


def validate_config():
    """Import and validate config"""
    try:
        from config import Config
        
        errors = Config.validate()
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        print("✅ Configuration valid")
        print(f"   Environment: {Config.KALSHI_ENV}")
        print(f"   Risk per trade: {Config.RISK_PER_TRADE_PCT:.1%}")
        print(f"   Max daily DD: {Config.MAX_DAILY_DRAWDOWN_PCT:.1%}")
        
        if Config.KALSHI_ENV != 'demo':
            print("\n⚠️ WARNING: You are configured for LIVE trading!")
            print("   Recommendation: Start with KALSHI_ENV=demo")
        
        return True
    except Exception as e:
        print(f"❌ Config validation failed: {e}")
        return False


def main():
    print("=" * 60)
    print("🤖 Kalshi Trading Bot - Setup Validation")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Configuration", validate_config),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n[{name}]")
        results.append(check_func())
        print()
    
    print("=" * 60)
    if all(results):
        print("✅ All checks passed! Ready to run bot.")
        print("\nNext steps:")
        print("1. python kalshi_bot.py  # Start bot in demo mode")
        print("2. Monitor logs and test with sandbox trading")
        print("3. Only switch to live after extensive testing")
    else:
        print("❌ Some checks failed. Fix issues above before running bot.")
        sys.exit(1)
    print("=" * 60)


if __name__ == '__main__':
    main()
