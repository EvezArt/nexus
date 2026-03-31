# Contributing to NEXUS

Thanks for your interest in contributing! NEXUS is an open-source project in the EVEZ ecosystem.

## How to contribute

### Report bugs
Open an issue with:
- What you did
- What happened
- What you expected
- Environment details (OS, Python version)

### Request features
Open an issue with:
- What you want
- Why you need it
- How you think it should work

### Submit code
1. Fork the repo
2. Create a branch: `git checkout -b my-feature`
3. Make your changes
4. Test: `python3 -m py_compile nexus/*.py`
5. Commit: `git commit -m "Add my feature"`
6. Push: `git push origin my-feature`
7. Open a Pull Request

### Add a provider
1. Create `nexus/providers/my_provider.py`
2. Extend `BaseProvider` from `providers/base.py`
3. Implement `chat()` and `format_messages()`
4. Register in `nexus/providers/__init__.py`
5. Add routing logic in `nexus_core.py`
6. Submit a PR

## Code style
- Python 3.11+
- Type hints encouraged
- Docstrings for public functions
- Keep functions small and focused

## License
By contributing, you agree your code will be licensed under the MIT License.
