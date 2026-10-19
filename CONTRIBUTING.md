# Contributing to Meta Nexus Agent

Thank you for contributing to **Meta Nexus Agent**!

## Development Setup
1. Fork and clone the repository.
2. Ensure `ffmpeg` is installed on your PATH.
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
4. Run the automated test suite:
   ```bash
   python -m pytest -v
   ```

## Guidelines
- Never commit `chrome_profile/` session cookies or `.env` secrets.
- Adhere to the **82-Rule Humanizer** for all caption and comment prompts.
- Include unit tests in `tests/test_meta_agent.py` for new features.
