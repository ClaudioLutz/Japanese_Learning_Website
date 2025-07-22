Below is a **one-page tracking checklist** that keeps the big picture in sight while showing exactly where you are today. Each line links to the relevant Google-Cloud doc so you can dig deeper only when you need to.

## Deployment master checklist

| #      | Task                                                                                               | Owner / where to run | Current status                                                                                   | Key reference       |
| ------ | -------------------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------ | ------------------- |
| **1**  | **Install Google Cloud CLI**                                                                       | **Windows laptop**   | ✅ Done (SDK 530.0.0) ([Google Cloud][1])                                                         |                     |
| **2**  | **Create & activate `prod` configuration**<br/>`gcloud config configurations create/activate prod` | Laptop               | ✅ Done (shows as active) ([Google Cloud][2])                                                     |                     |
| **3**  | **Set default project + zone**<br/>`gcloud config set project …` / `set compute/zone …`            | Laptop               | ✅ Done (`healthy-coil-466105-d7`, `europe-west6-c`) ([Google Cloud][1], [Google Cloud][2])       |                     |
| **4**  | **Authenticate account**<br/>`gcloud auth login`                                                   | Laptop               | ✅ Logged in as *[claudio.lutz.cv@gmail.com](mailto:claudio.lutz.cv@gmail.com)*                   |                     |
| **5**  | **Generate SSH key on first login**<br/>`gcloud compute ssh VM_NAME` → answer **Y**                | Laptop               | ⏳ Prompt shown; press **Y** → CLI makes key & opens shell ([Google Cloud][3], [Google Cloud][4]) |                     |
| **6**  | **(Optional) Copy ad-hoc files** with `gcloud compute scp`                                         | Laptop ↔ VM          | Not needed yet                                                                                   | ([Google Cloud][3]) |
| **7**  | **Download Cloud SQL Auth Proxy (signed Win binary ≥ v2.17.1)**                                    | Laptop               | ⬜ To do                                                                                          | ([Google Cloud][5]) |
| **8**  | **Start proxy for DB work**<br/>`cloud-sql-proxy --port 5432 PROJECT:REGION:INSTANCE`              | Laptop               | ⬜ To do                                                                                          | ([Google Cloud][6]) |
| **9**  | **Test DB access** with `psql` or Alembic pointing to `localhost:5432`                             | Laptop               | ⬜ To do                                                                                          | ([Google Cloud][6]) |
| **10** | **Deploy code to VM** (`git pull`)                                                                 | VM                   | ⬜ Pending after SSH key step                                                                     |                     |
| **11** | **Apply Alembic migrations** (`alembic upgrade head`)                                              | VM                   | ⬜ Pending (after proxy verified)                                                                 |                     |
| **12** | **Restart Gunicorn service**<br/>`sudo systemctl restart japanese_learning`                        | VM                   | ⬜ Pending                                                                                        |                     |
| **13** | **(Later) Set up HTTPS via Certbot**                                                               | VM                   | ⬜ Optional, next phase                                                                           |                     |

### How to resume

1. **Press `Y`** at the CLI prompt → you’ll be inside the VM (finishes step 5).
2. Do steps 7–9 on your laptop when you’re ready to work with the Cloud SQL database.
3. From inside the VM: pull code → run migrations → restart service (steps 10–12).

This keeps the goal clear and limits what you need to focus on right now. Once a box turns ✅, move to the next row.

[1]: https://cloud.google.com/sdk/gcloud/reference/config/configurations/create?utm_source=chatgpt.com "gcloud config configurations create - Google Cloud"
[2]: https://cloud.google.com/sdk/docs/configurations?utm_source=chatgpt.com "Managing gcloud CLI configurations - Google Cloud"
[3]: https://cloud.google.com/compute/docs/connect/create-ssh-keys?utm_source=chatgpt.com "Create SSH keys | Compute Engine Documentation | Google Cloud"
[4]: https://cloud.google.com/sdk/gcloud/reference/compute/ssh?utm_source=chatgpt.com "gcloud compute ssh | Google Cloud SDK Documentation"
[5]: https://cloud.google.com/sql/docs/sqlserver/sql-proxy?utm_source=chatgpt.com "About the Cloud SQL Auth Proxy"
[6]: https://cloud.google.com/sql/docs/mysql/connect-auth-proxy?utm_source=chatgpt.com "Connect using the Cloud SQL Auth Proxy"
