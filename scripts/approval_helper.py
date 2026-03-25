"""
Utility script to help with the approval workflow.
"""
import os
import sys
from pathlib import Path

def list_pending_approvals(vault_path):
    """List all pending approval files."""
    pending_dir = Path(vault_path) / "Pending_Approval"
    if not pending_dir.exists():
        print(f"No Pending_Approval directory found at {pending_dir}")
        return

    approval_files = list(pending_dir.glob("*.md"))
    if not approval_files:
        print("No pending approvals found.")
        return

    print(f"Found {len(approval_files)} pending approval(s):")
    for i, file in enumerate(approval_files, 1):
        print(f"  {i}. {file.name}")
        # Read first few lines to show content preview
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[:8]:  # Show first 8 lines
                print(f"      {line.rstrip()}")
        print()

def approve_item(vault_path, filename):
    """Move an approval file to the Approved folder."""
    src = Path(vault_path) / "Pending_Approval" / filename
    dst = Path(vault_path) / "Approved" / filename

    if not src.exists():
        print(f"File {filename} not found in Pending_Approval")
        return False

    dst.parent.mkdir(exist_ok=True)
    src.rename(dst)
    print(f"Approved: {filename} -> Approved/")
    return True

def reject_item(vault_path, filename):
    """Move an approval file to the Rejected folder."""
    src = Path(vault_path) / "Pending_Approval" / filename
    dst = Path(vault_path) / "Rejected" / filename

    if not src.exists():
        print(f"File {filename} not found in Pending_Approval")
        return False

    dst.parent.mkdir(exist_ok=True)
    src.rename(dst)
    print(f"Rejected: {filename} -> Rejected/")
    return True

def main():
    if len(sys.argv) < 2:
        print("Approval Workflow Helper")
        print("Usage:")
        print("  python approval_helper.py list <vault_path>          # List pending approvals")
        print("  python approval_helper.py approve <filename> <vault_path>  # Approve an item")
        print("  python approval_helper.py reject <filename> <vault_path>   # Reject an item")
        return

    command = sys.argv[1]
    if command == "list":
        if len(sys.argv) < 3:
            print("Please provide vault path")
            return
        list_pending_approvals(sys.argv[2])
    elif command in ["approve", "reject"]:
        if len(sys.argv) < 4:
            print(f"Please provide filename and vault path")
            return
        filename = sys.argv[2]
        vault_path = sys.argv[3]

        if command == "approve":
            approve_item(vault_path, filename)
        else:
            reject_item(vault_path, filename)
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()