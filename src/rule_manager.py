import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from .action_executor import Action


@dataclass
class Rule:
    id: str
    name: str
    image_path: str
    actions: list[Action]
    enabled: bool = True
    description: str = ""
    created_ts: int = 0  # unix timestamp
    # Priority (lower number = higher priority)
    priority: int = 100
    # Capture coordinates (x, y, width, height)
    capture_x: int = 0
    capture_y: int = 0
    capture_width: int = 0
    capture_height: int = 0
    # Monitor index (-1 = any)
    monitor_idx: int = -1
    # Rule condition type: "image" or "screen_unchanged"
    condition_type: str = "image"
    # For screen_unchanged condition: timeout in minutes
    screen_unchanged_timeout: float = 5.0
    # Window targeting
    target_window_title: str = ""  # Target window title (empty = any window)
    target_window_process: str = ""  # Target window process name (empty = any process)
    window_exact_match: bool = False  # Whether to match window title exactly
    # Enhanced window targeting
    target_window_class: str = ""  # Target window class name (Windows-specific)
    window_id_method: str = "auto"  # Method to identify window: "title", "process", "class", "auto"
    # Rule clustering for efficiency
    cluster_group: str = ""
    # Auto-disable triggers
    disable_after_executions: int = 0  # Disable rule after this many executions (0 = never)
    disable_on_image: str = ""  # Disable rule when this image is detected (empty = never)
    execution_count: int = (
        0  # Number of times this rule has been executed  # Rules with same cluster_group execute together
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "image_path": self.image_path,
            "actions": [action.to_dict() for action in self.actions],
            "enabled": self.enabled,
            "description": self.description,
            "created_ts": self.created_ts,
            "priority": self.priority,
            "capture_x": self.capture_x,
            "capture_y": self.capture_y,
            "capture_width": self.capture_width,
            "capture_height": self.capture_height,
            "monitor_idx": self.monitor_idx,
            "condition_type": self.condition_type,
            "screen_unchanged_timeout": self.screen_unchanged_timeout,
            "target_window_title": self.target_window_title,
            "target_window_process": self.target_window_process,
            "window_exact_match": self.window_exact_match,
            "target_window_class": self.target_window_class,
            "window_id_method": self.window_id_method,
            "cluster_group": self.cluster_group,
            "disable_after_executions": self.disable_after_executions,
            "disable_on_image": self.disable_on_image,
            "execution_count": self.execution_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Rule":
        actions = [Action.from_dict(action_data) for action_data in data.get("actions", [])]
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            image_path=data["image_path"],
            actions=actions,
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
            created_ts=data.get("created_ts", int(time.time())),
            priority=data.get("priority", 100),
            capture_x=data.get("capture_x", 0),
            capture_y=data.get("capture_y", 0),
            capture_width=data.get("capture_width", 0),
            capture_height=data.get("capture_height", 0),
            monitor_idx=data.get("monitor_idx", -1),
            condition_type=data.get("condition_type", "image"),
            screen_unchanged_timeout=data.get("screen_unchanged_timeout", 5.0),
            target_window_title=data.get("target_window_title", ""),
            target_window_process=data.get("target_window_process", ""),
            window_exact_match=data.get("window_exact_match", False),
            target_window_class=data.get("target_window_class", ""),
            window_id_method=data.get("window_id_method", "auto"),
            cluster_group=data.get("cluster_group", ""),
            disable_after_executions=data.get("disable_after_executions", 0),
            disable_on_image=data.get("disable_on_image", ""),
            execution_count=data.get("execution_count", 0),
        )


class RuleManager:
    def __init__(self, rules_dir: str = "data/rules"):
        self.rules_dir = rules_dir
        self.rules: dict[str, Rule] = {}
        self._ensure_rules_dir()
        self.load_all_rules()

    def _ensure_rules_dir(self):
        """Ensure the rules directory exists"""
        os.makedirs(self.rules_dir, exist_ok=True)

    def create_rule(
        self,
        name: str,
        image_path: str,
        actions: list[Action],
        description: str = "",
        condition_type: str = "image",
        screen_unchanged_timeout: float = 5.0,
    ) -> Rule:
        """Create a new rule"""
        rule_id = str(uuid.uuid4())
        rule = Rule(
            id=rule_id,
            name=name,
            image_path=image_path,
            actions=actions,
            description=description,
            created_ts=int(time.time()),
            condition_type=condition_type,
            screen_unchanged_timeout=screen_unchanged_timeout,
        )
        self.rules[rule_id] = rule
        self.save_rule(rule)
        return rule

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID"""
        return self.rules.get(rule_id)

    def get_rule_by_name(self, name: str) -> Optional[Rule]:
        """Get a rule by name"""
        for rule in self.rules.values():
            if rule.name == name:
                return rule
        return None

    def list_rules(self) -> list[Rule]:
        """Get all rules"""
        return list(self.rules.values())

    def list_enabled_rules(self) -> list[Rule]:
        """Get all enabled rules, sorted by priority"""
        rules = [rule for rule in self.rules.values() if rule.enabled]
        return sorted(rules, key=lambda r: r.priority)

    def get_rules_by_cluster(self) -> dict[str, list[Rule]]:
        """Group enabled rules by cluster_group for efficient execution"""
        clusters = {}
        enabled_rules = self.list_enabled_rules()

        for rule in enabled_rules:
            # Use a combination of cluster_group, window_title, and process for clustering
            cluster_key = self._get_cluster_key(rule)
            if cluster_key not in clusters:
                clusters[cluster_key] = []
            clusters[cluster_key].append(rule)

        return clusters

    def _get_cluster_key(self, rule: Rule) -> str:
        """Generate a cluster key for a rule based on its window targeting"""
        parts = []

        # Use explicit cluster group if set
        if rule.cluster_group:
            parts.append(f"cluster:{rule.cluster_group}")

        # Add window targeting info
        if rule.target_window_title:
            parts.append(f"title:{rule.target_window_title}")
        elif rule.target_window_process:
            parts.append(f"process:{rule.target_window_process}")
        else:
            parts.append("any_window")

        return "|".join(parts) if parts else "default"

    def get_rules_by_window_target(
        self, window_title: str = "", window_process: str = ""
    ) -> list[Rule]:
        """Get rules that target a specific window"""
        enabled_rules = self.list_enabled_rules()
        matching_rules = []

        for rule in enabled_rules:
            if self._rule_matches_window(rule, window_title, window_process):
                matching_rules.append(rule)

        return matching_rules

    def _rule_matches_window(
        self, rule: Rule, window_title: str, window_process: str, window_class: str = ""
    ) -> bool:
        """Check if a rule matches the given window"""
        # If rule has no window targeting, it matches any window
        if (
            not rule.target_window_title
            and not rule.target_window_process
            and not rule.target_window_class
        ):
            return True

        # Determine matching method
        method = rule.window_id_method.lower()

        # Auto method: try all available targeting methods
        if method == "auto":
            # Check window title match if specified
            if rule.target_window_title:
                if rule.window_exact_match:
                    if rule.target_window_title != window_title:
                        return False
                else:
                    if rule.target_window_title.lower() not in window_title.lower():
                        return False

            # Check process match if specified
            if rule.target_window_process:
                if rule.target_window_process.lower() not in window_process.lower():
                    return False

            # Check class match if specified
            if rule.target_window_class and window_class:
                if rule.target_window_class.lower() not in window_class.lower():
                    return False

            return True

        # Title-only method
        elif method == "title" and rule.target_window_title:
            if rule.window_exact_match:
                return rule.target_window_title == window_title
            else:
                return rule.target_window_title.lower() in window_title.lower()

        # Process-only method
        elif method == "process" and rule.target_window_process:
            return rule.target_window_process.lower() in window_process.lower()

        # Class-only method
        elif method == "class" and rule.target_window_class and window_class:
            return rule.target_window_class.lower() in window_class.lower()

        # Fallback to auto method if specified method doesn't have required data
        else:
            # Check window title match if specified
            if rule.target_window_title:
                if rule.window_exact_match:
                    if rule.target_window_title != window_title:
                        return False
                else:
                    if rule.target_window_title.lower() not in window_title.lower():
                        return False

            # Check process match if specified
            if rule.target_window_process:
                if rule.target_window_process.lower() not in window_process.lower():
                    return False

            # Check class match if specified
            if rule.target_window_class and window_class:
                if rule.target_window_class.lower() not in window_class.lower():
                    return False

            return True

    def list_rules_by_priority(self) -> list[Rule]:
        """Get all rules sorted by priority"""
        return sorted(self.rules.values(), key=lambda r: r.priority)

    def update_rule(self, rule_id: str, **kwargs) -> bool:
        """Update a rule"""
        if rule_id not in self.rules:
            return False

        rule = self.rules[rule_id]

        # Check if rule is being enabled and reset execution counter
        if "enabled" in kwargs and kwargs["enabled"] and not rule.enabled:
            # Rule is being enabled from disabled state - reset execution counter
            kwargs["execution_count"] = 0

        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        self.save_rule(rule)
        return True

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        if rule_id not in self.rules:
            return False

        self.rules[rule_id]
        rule_file = os.path.join(self.rules_dir, f"{rule_id}.json")

        # Remove from memory
        del self.rules[rule_id]

        # Remove file
        if os.path.exists(rule_file):
            os.remove(rule_file)

        return True

    def save_rule(self, rule: Rule):
        """Save a rule to file"""
        rule_file = os.path.join(self.rules_dir, f"{rule.id}.json")
        with open(rule_file, "w") as f:
            json.dump(rule.to_dict(), f, indent=2)

    def load_rule(self, rule_id: str) -> Optional[Rule]:
        """Load a rule from file"""
        rule_file = os.path.join(self.rules_dir, f"{rule_id}.json")
        if not os.path.exists(rule_file):
            return None

        try:
            with open(rule_file) as f:
                data = json.load(f)
            rule = Rule.from_dict(data)
            self.rules[rule.id] = rule
            return rule
        except Exception as e:
            print(f"Error loading rule {rule_id}: {e}")
            return None

    def load_all_rules(self):
        """Load all rules from the rules directory"""
        if not os.path.exists(self.rules_dir):
            return

        for filename in os.listdir(self.rules_dir):
            if filename.endswith(".json"):
                rule_id = filename[:-5]  # Remove .json extension
                self.load_rule(rule_id)

    def export_rules(self, filepath: str):
        """Export all rules to a single JSON file"""
        rules_data = [rule.to_dict() for rule in self.rules.values()]
        with open(filepath, "w") as f:
            json.dump(rules_data, f, indent=2)

    def import_rules(self, filepath: str) -> int:
        """Import rules from a JSON file. Returns number of imported rules."""
        try:
            with open(filepath) as f:
                rules_data = json.load(f)

            imported_count = 0
            for rule_data in rules_data:
                try:
                    rule = Rule.from_dict(rule_data)
                    # Generate new ID to avoid conflicts
                    rule.id = str(uuid.uuid4())
                    self.rules[rule.id] = rule
                    self.save_rule(rule)
                    imported_count += 1
                except Exception as e:
                    print(f"Error importing rule: {e}")
                    continue

            return imported_count
        except Exception as e:
            print(f"Error importing rules from {filepath}: {e}")
            return 0

    # ------------------------------------------------------------------
    # SA-27 – Conflict detection
    def detect_conflicts(self) -> list[tuple[Rule, Rule, str]]:
        """Return list of conflicts as tuples (rule1, rule2, reason). Only considers enabled rules."""
        conflicts: list[tuple[Rule, Rule, str]] = []
        enabled_rules = self.list_enabled_rules()
        n = len(enabled_rules)

        def _rect(rule: Rule):
            return (
                (
                    rule.capture_x,
                    rule.capture_y,
                    rule.capture_x + rule.capture_width,
                    rule.capture_y + rule.capture_height,
                )
                if rule.capture_width and rule.capture_height
                else None
            )

        def _rects_overlap(a, b):
            if not a or not b:
                return False
            ax1, ay1, ax2, ay2 = a
            bx1, by1, bx2, by2 = b
            return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1

        for i in range(n):
            r1 = enabled_rules[i]
            for j in range(i + 1, n):
                r2 = enabled_rules[j]
                reason = None
                # Same trigger image
                if r1.image_path and r1.image_path == r2.image_path:
                    reason = "Same trigger image"
                else:
                    # Overlapping capture regions
                    if _rects_overlap(_rect(r1), _rect(r2)):
                        reason = "Overlapping capture region"
                if reason:
                    conflicts.append((r1, r2, reason))
        return conflicts
