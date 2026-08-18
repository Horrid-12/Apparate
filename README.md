# Apparate

Apparate is an automated utility to synchronize your accepted HackerRank solutions directly to a designated GitHub repository.

This project is a modernized fork of the original Apparate utility by [Sanket Gautam](https://github.com/sanketgautam/Apparate), updated with modern browser automation, secure state management, and a native desktop interface.

---

## Key Features

- **Dual Interfaces**: Use either the native desktop GUI or the command-line interface (CLI).
- **Modern Automation**: Powered by Playwright for fast, reliable browser automation without manual driver setup.
- **Flexible Authentication**: Sign in via credentials or launch your system browser for Google, GitHub, or Single Sign-On (SSO) login.
- **Secure State Persistence**: Tracks synchronized submissions using standard `json` stored directly in your GitHub repository, replacing insecure legacy serialization.
- **Local Processing**: All code extraction and processing occurs locally on your machine without third-party network proxies.
- **Standalone Binary**: Includes an automated build script to compile a portable Windows `.exe` application.

---

## Desktop GUI

Apparate includes a native desktop application with a neutral dark interface and Inter typography.

### Running from Source
```bash
python apparate_gui.py
```

### Running the Standalone Executable
You can run the pre-built executable directly:
```
dist/Apparate.exe
```

### Building the Executable
To rebuild the standalone Windows binary, run the automated build script:
```bash
python build.py
```
Or double-click `build.bat` on Windows. The script automatically handles process management, cleans previous build artifacts, and outputs `dist/Apparate.exe`.

---

## Command Line Interface (CLI)

Apparate can also be executed directly via terminal or scheduled via cron.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Horrid-12/Apparate.git
   cd Apparate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

### Usage
```bash
apparate --repo <Submissions_Repo_Name> --user <HackerRank_Username> --passwd <HackerRank_Password> --token <GitHub_Token>
```

### Options
```
Usage: apparate [OPTIONS]

Options:
  --repo TEXT    Name of GitHub repository to store submissions
  --user TEXT    Username of your HackerRank account
  --passwd TEXT  Login password of your HackerRank account
  --token TEXT   GitHub Personal Access Token with 'repo' scope
  --help         Show this message and exit.
```

---

## GitHub Access Token Setup

To allow Apparate to create and update your solutions repository:
1. Go to **GitHub Settings** -> **Developer Settings** -> **Personal Access Tokens** -> **Tokens (classic)**.
2. Generate a new token with the `repo` scope.
3. Use this token in the GUI or pass it to the `--token` CLI argument.

---

## Architecture Overview

- **`scripts/apparate.py`**: Core orchestrator managing GitHub API operations, repository creation, commit workflows, and submission state tracking (`submissions.json`).
- **`scripts/spider.py`**: Browser automation layer using Playwright for HackerRank session handling, submission pagination traversal, and code extraction.
- **`apparate_gui.py`**: Native desktop GUI built with Tkinter, featuring live log streaming, credential caching, and browser selection.
- **`build.py` / `build.bat`**: Automated PyInstaller packaging pipeline.

---

## Credits and Acknowledgments

- Original concept and implementation by **[Sanket Gautam](https://github.com/sanketgautam)**: [sanketgautam/Apparate](https://github.com/sanketgautam/Apparate)
- Modernized and maintained by **[Horrid-12](https://github.com/Horrid-12/Apparate)**

---

## License

This project is open-source under the MIT License.
