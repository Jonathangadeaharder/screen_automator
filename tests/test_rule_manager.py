
from src.action_executor import create_click_action
from src.rule_manager import RuleManager


def test_create_and_save_rule(tmp_path):
    rm = RuleManager(rules_dir=str(tmp_path))
    action = create_click_action(10, 20)
    rule = rm.create_rule("test", image_path="", actions=[action])

    assert rule.id in rm.rules
    saved_path = tmp_path / f"{rule.id}.json"
    assert saved_path.exists()


def test_monitor_idx_persistence(tmp_path):
    rm = RuleManager(rules_dir=str(tmp_path))
    r = rm.create_rule("mon", image_path="", actions=[])
    rm.update_rule(r.id, monitor_idx=1)

    # reload
    new_rm = RuleManager(rules_dir=str(tmp_path))
    loaded = new_rm.get_rule(r.id)
    assert loaded.monitor_idx == 1
