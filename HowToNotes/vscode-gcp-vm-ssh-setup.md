# VS Code Remote SSH Setup for GCP VMs

## Current VM Configuration

**Project ID:** `jpl-website-bill-20251130`  
**Zone:** `europe-west6-c`

### Available VMs:
1. **japanese-learning-website** (Currently TERMINATED)
2. **japanese-learning-website-neu** (Currently TERMINATED)

Both VMs have no external IPs, so we'll use **IAP (Identity-Aware Proxy)** for secure SSH access.

---

## Prerequisites

1. **VS Code** installed on your laptop
2. **Remote - SSH** extension installed in VS Code
3. **gcloud CLI** already installed and authenticated (✓ You have this)
4. IAP access enabled for your project

---

## Step 1: Enable IAP TCP Forwarding

Run this command to ensure IAP is enabled:

```bash
gcloud services enable iap.googleapis.com --project=jpl-website-bill-20251130
```

## Step 2: Create Firewall Rule for IAP SSH Access

```bash
gcloud compute firewall-rules create allow-ssh-from-iap \
    --project=jpl-website-bill-20251130 \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:22 \
    --source-ranges=35.235.240.0/20 \
    --target-tags=allow-ssh-from-iap
```

If this rule already exists, you can skip this step or update the VMs to use the tag.

## Step 3: Configure SSH Config File

### For Windows (PowerShell):

Add this to your SSH config file at `C:\Users\<YourUsername>\.ssh\config`:

```ssh
# Japanese Learning Website VM (original)
Host japanese-learning-website
  HostName japanese-learning-website
  User <your-linux-username>
  IdentityFile ~/.ssh/google_compute_engine
  ProxyCommand gcloud compute start-iap-tunnel %h %p --listen-on-stdin --project=jpl-website-bill-20251130 --zone=europe-west6-c
  StrictHostKeyChecking no
  UserKnownHostsFile=/dev/null

# Japanese Learning Website VM (neu)
Host japanese-learning-website-neu
  HostName japanese-learning-website-neu
  User <your-linux-username>
  IdentityFile ~/.ssh/google_compute_engine
  ProxyCommand gcloud compute start-iap-tunnel %h %p --listen-on-stdin --project=jpl-website-bill-20251130 --zone=europe-west6-c
  StrictHostKeyChecking no
  UserKnownHostsFile=/dev/null
```

**Note:** Replace `<your-linux-username>` with your actual Linux username on the VMs.

### To find your Linux username:

If you're not sure of your username, it's typically:
- Your Google account username (before @gmail.com)
- Or you can check after starting the VM with: `gcloud compute ssh japanese-learning-website --zone=europe-west6-c` and it will show you

---

## Step 4: Start Your VM

Before connecting, you need to start the VM (since both are currently terminated):

```bash
# Start the original VM
gcloud compute instances start japanese-learning-website --zone=europe-west6-c

# OR start the newer VM
gcloud compute instances start japanese-learning-website-neu --zone=europe-west6-c
```

Wait about 30 seconds for the VM to fully boot.

---

## Step 5: Connect from VS Code

1. Open VS Code
2. Press `F1` or `Ctrl+Shift+P` to open the command palette
3. Type and select: **Remote-SSH: Connect to Host...**
4. Choose either:
   - `japanese-learning-website`
   - `japanese-learning-website-neu`
5. VS Code will connect and install the VS Code Server on the VM automatically
6. Once connected, you can:
   - Open folders on the VM
   - Use the integrated terminal (running on the VM)
   - Edit files directly on the VM
   - Debug applications running on the VM

---

## Troubleshooting

### Issue: "Permission denied (publickey)"

Generate or ensure SSH keys exist:

```bash
# Generate Google Compute SSH keys if they don't exist
ssh-keygen -t rsa -f ~/.ssh/google_compute_engine -C <your-email>
```

Then add the public key to your VM:

```bash
gcloud compute os-login ssh-keys add --key-file ~/.ssh/google_compute_engine.pub
```

### Issue: IAP tunnel fails

1. Ensure the VM is running: `gcloud compute instances list`
2. Check IAP is enabled: `gcloud services list --enabled | grep iap`
3. Verify you have IAP permissions: `gcloud projects get-iam-policy jpl-website-bill-20251130 --flatten="bindings[].members" --format='table(bindings.role)' --filter="bindings.members:user:<your-email>"`

### Issue: Connection timeout

- VMs may take 30-60 seconds to boot after starting
- Check VM status: `gcloud compute instances describe japanese-learning-website --zone=europe-west6-c | grep status`

---

## Quick Commands Reference

```bash
# List all VMs and their status
gcloud compute instances list

# Start a VM
gcloud compute instances start japanese-learning-website --zone=europe-west6-c

# Stop a VM (to save costs)
gcloud compute instances stop japanese-learning-website --zone=europe-west6-c

# SSH directly via gcloud (alternative to VS Code)
gcloud compute ssh japanese-learning-website --zone=europe-west6-c

# Check VM details
gcloud compute instances describe japanese-learning-website --zone=europe-west6-c
```

---

## Alternative: Using Cloud Code Extension

If you install the **Cloud Code** extension for VS Code:

1. It can automatically list all your GCP VMs
2. You can start/stop VMs from within VS Code
3. You can connect to VMs with one click
4. It handles IAP tunneling automatically

Install from VS Code extensions: Search for "Cloud Code"

---

## Cost Considerations

- **e2-micro** instances cost approximately $7-8/month when running continuously
- Remember to **stop VMs when not in use** to save costs
- You can set up auto-shutdown schedules in GCP Console

---

## Next Steps

1. Run the IAP enable command (Step 1)
2. Create/update your SSH config file (Step 3)
3. Start the VM you want to use (Step 4)
4. Connect from VS Code (Step 5)

Once connected, all your development work will happen on the VM, with the full VS Code UI running locally on your laptop.
