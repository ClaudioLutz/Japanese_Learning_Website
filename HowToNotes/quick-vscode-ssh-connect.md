# Quick VS Code SSH Connection Guide

## ✅ Setup Complete!

Your VM is now running and ready to connect:

**VM:** japanese-learning-website-neu
**Status:** RUNNING
**Internal IP:** 10.172.0.3
**External IP:** 34.65.164.3
**Zone:** europe-west6-c

---

## Connect to VM from VS Code

### Step 1: Open VS Code

### Step 2: Open Command Palette
- Press `F1` or `Ctrl+Shift+P`

### Step 3: Connect to Host
1. Type: **Remote-SSH: Connect to Host...**
2. Select it from the dropdown
3. Choose: **japanese-learning-website-neu**

### Step 4: First Connection
- VS Code will open a new window
- It will install VS Code Server on the VM (takes 1-2 minutes on first connection)
- You may be asked to select the platform - choose **Linux**

### Step 5: You're Connected!
Once connected, you'll see "SSH: japanese-learning-website-neu" in the bottom-left corner of VS Code.

---

## What You Can Do Now

1. **Open Folder on VM**: 
   - File > Open Folder
   - Navigate to your project directory on the VM

2. **Open Terminal on VM**:
   - Terminal > New Terminal
   - This runs commands directly on the VM

3. **Edit Files**:
   - All files you open/edit are on the VM
   - Changes are instant on the remote machine

4. **Install Extensions on VM**:
   - Some extensions need to be installed on the remote machine
   - VS Code will prompt you to install them there

---

## Troubleshooting

### If connection fails:

1. **Check VM is running**:
   ```powershell
   gcloud compute instances list
   ```

2. **Try connecting via gcloud first**:
   ```powershell
   gcloud compute ssh japanese-learning-website-neu --zone=europe-west6-c
   ```
   This will show you your actual Linux username on the VM.

3. **Update SSH config with correct username**:
   If the username is different from "claud", edit:
   `C:\Users\claud\.ssh\config`
   And change the `User` line to match your actual VM username.

### If you see "Permission denied (publickey)":

Run this to add your SSH key:
```powershell
gcloud compute ssh japanese-learning-website-neu --zone=europe-west6-c
```
This will automatically set up the SSH keys for you.

---

## Stop VM When Done (Save Costs)

When you're finished working:

```powershell
gcloud compute instances stop japanese-learning-website-neu --zone=europe-west6-c
```

To start it again next time:
```powershell
gcloud compute instances start japanese-learning-website-neu --zone=europe-west6-c
```

---

## Alternative Connection Methods

### Method 1: Use Cloud Code Extension
- Install "Cloud Code" extension in VS Code
- It provides a GUI to manage and connect to VMs
- Automatically handles IAP tunneling

### Method 2: Direct gcloud SSH
```powershell
gcloud compute ssh japanese-learning-website-neu --zone=europe-west6-c
```

### Method 3: VS Code with External IP
Since your VM has an external IP (34.65.164.3), you could also use direct SSH, but IAP is more secure.

---

## Your Current Setup Summary

✅ IAP enabled for secure access  
✅ Firewall rule created for SSH  
✅ SSH config file configured  
✅ VM started and running  
✅ Ready to connect from VS Code

**Next Step:** Open VS Code and press F1 → "Remote-SSH: Connect to Host..." → Select "japanese-learning-website-neu"
