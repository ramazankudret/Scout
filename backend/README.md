# Scout Backend

## Prerequisites

- Python 3.11 or 3.12 (3.14 not supported by asyncpg).
- **Nmap** – required for Hunter subnet/port scans. Install on Windows:

  **Option A – Chocolatey (recommended)**  
  Run PowerShell as Administrator:
  ```powershell
  choco install nmap
  refreshenv
  ```

  **Option B – Manual**  
  Download the Windows installer from [nmap.org/download](https://nmap.org/download.html), install, then add the install folder (e.g. `C:\Program Files (x86)\Nmap`) to your system PATH.

  Verify: `nmap --version`