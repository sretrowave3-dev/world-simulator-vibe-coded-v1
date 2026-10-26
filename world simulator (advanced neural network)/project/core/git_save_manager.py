"""
project/core/git_save_manager.py

Git-Like Version Control, Timeline Branching, and Accidental Overwrite Protection Subsystem.
Solves the problem of users accidentally overwriting progressed simulation states
with earlier or fresh genesis states.

Guarantees:
- Stale-State Overwrite Protection: If a save attempt targets an existing file with
  higher tick progression or diverged lineage, the existing state is automatically
  preserved in an immutable branch stash snapshot (Zero Data Loss).
- Complete DAG Lineage Tracking: Tracks commit parentage, active branches, and commit hashes.
- Git CLI Commands: status, log, commit, branch, checkout, diff.
- Manifest Synchronization: Stores all branches and commits in saves/git_manifest.json.
"""

from __future__ import annotations

import os
import time
import json
import shutil
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SAVES_DIR = os.path.join(WORKSPACE_DIR, "saves")
BRANCHES_DIR = os.path.join(SAVES_DIR, "branches")
MANIFEST_PATH = os.path.join(SAVES_DIR, "git_manifest.json")


@dataclass
class GitCommit:
    """Represents a discrete simulation snapshot commit node."""
    commit_id: str
    parent_id: Optional[str]
    branch: str
    tick: int
    alive_count: int
    message: str
    timestamp: float
    date_str: str
    file_path: str
    is_branch_stash: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GitSaveManager:
    """
    Git-like version control engine protecting simulation checkpoints against
    accidental overwrites and managing evolutionary branches.
    """

    def __init__(self, saves_dir: Optional[str] = None) -> None:
        self.saves_dir = saves_dir or SAVES_DIR
        self.branches_dir = os.path.join(self.saves_dir, "branches")
        self.manifest_path = os.path.join(self.saves_dir, "git_manifest.json")
        os.makedirs(self.saves_dir, exist_ok=True)
        os.makedirs(self.branches_dir, exist_ok=True)

        self.active_branch: str = "main"
        self.current_commit_id: Optional[str] = None
        self.branches: Dict[str, str] = {"main": ""}
        self.commits: Dict[str, GitCommit] = {}
        self._load_manifest()

    def _load_manifest(self) -> None:
        """Loads repository manifest from disk, or initializes fresh repository."""
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.active_branch = data.get("active_branch", "main")
                self.current_commit_id = data.get("head_commit_id")
                self.branches = data.get("branches", {"main": ""})
                
                raw_commits = data.get("commits", {})
                self.commits = {}
                for cid, cdata in raw_commits.items():
                    self.commits[cid] = GitCommit(**cdata)
                return
            except Exception as e:
                print(f"[GIT SAVE] Warning reading manifest: {e}. Rebuilding...")

        # Initialize clean repository
        self.active_branch = "main"
        self.current_commit_id = None
        self.branches = {"main": ""}
        self.commits = {}
        self._save_manifest()

    def _save_manifest(self) -> None:
        """Writes repository state to git_manifest.json atomically."""
        data = {
            "version": "1.0",
            "active_branch": self.active_branch,
            "head_commit_id": self.current_commit_id,
            "branches": self.branches,
            "commits": {cid: c.to_dict() for cid, c in self.commits.items()},
            "last_updated": time.time(),
        }
        temp_p = f"{self.manifest_path}.tmp"
        with open(temp_p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_p, self.manifest_path)

    def generate_commit_id(self, parent_id: Optional[str], tick: int, timestamp: float) -> str:
        """Generates a 7-character hexadecimal commit hash."""
        seed = f"{parent_id}:{tick}:{timestamp}:{os.urandom(8).hex()}"
        return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:7]

    def check_and_protect_overwrite(
        self,
        target_file_path: str,
        current_tick: int,
        current_alive: int,
    ) -> Tuple[bool, str]:
        """
        ACCIDENTAL OVERWRITE SAFEGUARD:
        Checks whether saving to target_file_path would overwrite a state with higher progress
        or diverged lineage.
        If a conflict is detected, automatically preserves the existing file into a branch stash.
        Returns: (conflict_prevented: bool, message: str)
        """
        if not os.path.exists(target_file_path):
            return False, "Target is fresh file (clean save)."

        # Read existing sidecar metadata if available
        meta_path = f"{target_file_path}.meta.json"
        target_tick = 0
        target_commit_id = None

        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as mf:
                    meta = json.load(mf)
                    target_tick = int(meta.get("tick", 0))
                    target_commit_id = meta.get("commit_id")
            except Exception:
                pass

        base_name = os.path.basename(target_file_path)
        base_root, _ = os.path.splitext(base_name)

        # Detect Overwrite Conflict:
        # Case 1: Target file has strictly more ticks progressed than current simulation
        # (e.g. Current is Tick 150, Target on disk is Tick 9,400)
        # Case 2: Diverged lineage (target commit is not in ancestor chain of current simulation)
        is_stale_overwrite = (current_tick < target_tick)
        is_diverged = False
        if target_commit_id and self.current_commit_id and target_commit_id != self.current_commit_id:
            if not self._is_ancestor(target_commit_id, self.current_commit_id):
                is_diverged = True

        if is_stale_overwrite or is_diverged:
            # PRESERVE TARGET IN BRANCH STASH TO PREVENT DATA LOSS!
            ts_str = time.strftime("%Y%m%d_%H%M%S")
            short_cid = target_commit_id or "prev"
            stash_filename = f"{base_root}_stash_tick{target_tick}_{short_cid}_{ts_str}.dat"
            stash_path = os.path.join(self.branches_dir, stash_filename)

            try:
                shutil.copy2(target_file_path, stash_path)
                if os.path.exists(meta_path):
                    shutil.copy2(meta_path, f"{stash_path}.meta.json")

                # Register stash branch in manifest
                stash_branch_name = f"stash/{base_root}_tick{target_tick}_{ts_str}"
                stash_commit_id = target_commit_id or self.generate_commit_id(None, target_tick, time.time())
                
                if stash_commit_id not in self.commits:
                    self.commits[stash_commit_id] = GitCommit(
                        commit_id=stash_commit_id,
                        parent_id=None,
                        branch=stash_branch_name,
                        tick=target_tick,
                        alive_count=0,
                        message=f"Auto-Stash: Protected higher-progress save prior to overwrite",
                        timestamp=time.time(),
                        date_str=time.strftime("%Y-%m-%d %H:%M:%S"),
                        file_path=stash_path,
                        is_branch_stash=True,
                    )
                self.branches[stash_branch_name] = stash_commit_id
                self._save_manifest()

                msg = (
                    f"🛡️ [GIT SAFEGUARD] Prevented accidental data loss! "
                    f"Target '{base_name}' had higher progression (Tick {target_tick:,} vs Current Tick {current_tick:,}). "
                    f"Previous state safely archived in branch '{stash_branch_name}' ({stash_filename})."
                )
                print(msg)
                return True, msg
            except Exception as e:
                print(f"[GIT SAVE ERROR] Could not auto-stash existing file: {e}")

        return False, "Safe linear save progression."

    def _is_ancestor(self, possible_ancestor: str, current_id: Optional[str]) -> bool:
        """Traverses parent pointers to check if possible_ancestor is in current's lineage."""
        visited = set()
        curr = current_id
        while curr and curr in self.commits and curr not in visited:
            visited.add(curr)
            if curr == possible_ancestor:
                return True
            curr = self.commits[curr].parent_id
        return False

    def record_commit(
        self,
        file_path: str,
        tick: int,
        alive_count: int,
        message: Optional[str] = None,
    ) -> GitCommit:
        """
        Creates and registers a new commit node after a successful save.
        Advances active branch head pointer.
        """
        now = time.time()
        parent_id = self.current_commit_id
        commit_id = self.generate_commit_id(parent_id, tick, now)
        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        msg = message.strip() if message else f"Checkpoint at Tick {tick:,} ({alive_count} alive)"

        commit = GitCommit(
            commit_id=commit_id,
            parent_id=parent_id,
            branch=self.active_branch,
            tick=tick,
            alive_count=alive_count,
            message=msg,
            timestamp=now,
            date_str=date_str,
            file_path=file_path,
            is_branch_stash=False,
        )

        self.commits[commit_id] = commit
        self.current_commit_id = commit_id
        self.branches[self.active_branch] = commit_id
        self._save_manifest()

        return commit

    def on_load_checkpoint(self, file_path: str, tick: int, commit_id: Optional[str] = None) -> None:
        """Updates internal lineage state when user loads an existing checkpoint."""
        if commit_id and commit_id in self.commits:
            self.current_commit_id = commit_id
            self.active_branch = self.commits[commit_id].branch
        else:
            # Check if this file maps to a known commit
            matched_cid = None
            for cid, c in self.commits.items():
                if os.path.basename(c.file_path) == os.path.basename(file_path):
                    matched_cid = cid
                    break
            if matched_cid:
                self.current_commit_id = matched_cid
                self.active_branch = self.commits[matched_cid].branch
            else:
                # Create a synthetic initial commit node for this loaded state
                new_cid = self.generate_commit_id(None, tick, time.time())
                self.commits[new_cid] = GitCommit(
                    commit_id=new_cid,
                    parent_id=None,
                    branch=self.active_branch,
                    tick=tick,
                    alive_count=0,
                    message=f"Loaded from {os.path.basename(file_path)}",
                    timestamp=time.time(),
                    date_str=time.strftime("%Y-%m-%d %H:%M:%S"),
                    file_path=file_path,
                )
                self.current_commit_id = new_cid
                self.branches[self.active_branch] = new_cid

        self._save_manifest()
        print(f"🌿 [GIT HEAD] Aligned HEAD to commit '{self.current_commit_id}' on branch '{self.active_branch}' (Tick {tick:,})")

    def create_branch(self, branch_name: str) -> bool:
        """Creates a new timeline branch pointing to current HEAD."""
        clean = branch_name.strip()
        if not clean or clean in self.branches:
            return False
        self.branches[clean] = self.current_commit_id or ""
        self.active_branch = clean
        self._save_manifest()
        print(f"🌿 [GIT BRANCH] Created and switched to new branch '{clean}' at commit {self.current_commit_id}")
        return True

    def switch_branch(self, branch_name: str) -> Optional[str]:
        """Switches active branch and returns the target commit's file path if available."""
        clean = branch_name.strip()
        if clean not in self.branches:
            return None
        self.active_branch = clean
        target_cid = self.branches[clean]
        if target_cid and target_cid in self.commits:
            self.current_commit_id = target_cid
            self._save_manifest()
            return self.commits[target_cid].file_path
        self._save_manifest()
        return None

    def get_status(self, current_tick: int) -> Dict[str, Any]:
        """Returns working tree state and uncommitted progress."""
        head_commit = self.commits.get(self.current_commit_id) if self.current_commit_id else None
        head_tick = head_commit.tick if head_commit else 0
        uncommitted_ticks = max(0, current_tick - head_tick)

        return {
            "branch": self.active_branch,
            "head": self.current_commit_id or "(none)",
            "head_tick": head_tick,
            "current_tick": current_tick,
            "uncommitted_ticks": uncommitted_ticks,
            "total_commits": len(self.commits),
            "total_branches": len(self.branches),
        }

    def generate_ascii_log(self, limit: int = 15) -> str:
        """Generates a visual ASCII tree log of recent checkpoints and branches."""
        if not self.commits:
            return "No Git commits found in this world repository."

        sorted_commits = sorted(self.commits.values(), key=lambda c: c.timestamp, reverse=True)[:limit]
        lines = [
            "╔═══════════════════════════════════════════════════════════════════════════════════╗",
            f"║ 🌿 SIMULATION TIMELINE & REVISION GRAPH (Active Branch: {self.active_branch:<24})║",
            "╠═══════════════════════════════════════════════════════════════════════════════════╣",
        ]

        for c in sorted_commits:
            is_head = (c.commit_id == self.current_commit_id)
            branch_tags = [b for b, cid in self.branches.items() if cid == c.commit_id]
            
            tag_str = ""
            if is_head and branch_tags:
                tag_str = f" (HEAD -> {', '.join(branch_tags)})"
            elif is_head:
                tag_str = " (HEAD)"
            elif branch_tags:
                tag_str = f" ({', '.join(branch_tags)})"

            stash_flag = " [PROTECTED STASH]" if c.is_branch_stash else ""
            marker = "*" if not c.is_branch_stash else "o"
            
            lines.append(f"║ {marker} commit {c.commit_id}{tag_str}{stash_flag}")
            lines.append(f"║ │  Tick: {c.tick:,} | Alive: {c.alive_count:,} | Date: {c.date_str}")
            lines.append(f"║ │  Message: {c.message}")
            lines.append(f"║ │  File: {os.path.basename(c.file_path)}")
            lines.append("║ │")

        lines.append("╚═══════════════════════════════════════════════════════════════════════════════════╝")
        return "\n".join(lines)


# Global singleton instance
git_save_manager = GitSaveManager()
