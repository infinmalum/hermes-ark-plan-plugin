import dataclasses
import pathlib
import re
import runpy
import sys
import types
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / '__init__.py').read_text()


@dataclasses.dataclass
class Profile:
    name: str
    aliases: tuple
    display_name: str
    description: str
    signup_url: str
    api_mode: str
    env_vars: tuple
    base_url: str
    auth_type: str
    supports_model_listing: bool
    supports_health_check: bool
    fallback_models: tuple
    models_url: str = ""


class PluginTests(unittest.TestCase):
    def setUp(self):
        profiles = []
        registry = types.ModuleType('providers')
        setattr(registry, "register_provider", profiles.append)
        base = types.ModuleType('providers.base')
        setattr(base, "ProviderProfile", Profile)
        with patch.dict(sys.modules, {'providers': registry, 'providers.base': base}):
            self.module = runpy.run_path(str(ROOT / '__init__.py'))
        self.profiles = {p.name: p for p in profiles}
        self.coding = self.profiles['ark-coding-plan']

    def test_two_openai_compatible_profiles(self):
        self.assertEqual(set(self.profiles), {'ark-agentplan', 'ark-coding-plan'})
        self.assertEqual(self.profiles['ark-agentplan'].api_mode, 'codex_responses')
        self.assertEqual(self.coding.api_mode, 'chat_completions')

    def test_no_model_id_is_hardcoded(self):
        for profile in self.profiles.values():
            self.assertEqual(profile.fallback_models, ())
        literal = re.compile(r'"([a-z0-9][a-z0-9.-]*\d[a-z0-9.-]*)"')
        # "utf-8" is an encoding, not a model id; anything else numeric-looking is banned.
        found = [m for m in literal.findall(SOURCE) if m != 'utf-8']
        self.assertEqual(found, [])

    def test_agent_plan_has_no_catalog_and_manual_models(self):
        agent = self.profiles['ark-agentplan']
        self.assertIn('ark-plan', agent.aliases)
        self.assertFalse(agent.supports_model_listing)
        self.assertEqual(agent.env_vars, ('ARK_PLAN_API_KEY',))
        self.assertEqual(agent.base_url, 'https://ark.cn-beijing.volces.com/api/plan/v3')

    def test_coding_plan_reads_live_catalog(self):
        self.assertTrue(self.coding.supports_model_listing)
        self.assertEqual(self.coding.env_vars, ('ARK_CODING_API_KEY',))
        self.assertEqual(self.coding.base_url, 'https://ark.cn-beijing.volces.com/api/coding/v3')
        rows = [
            {"id": "live-text", "status": "", "modalities": {"output_modalities": ["text"]}},
            {"id": "retiring-text", "status": "Retiring", "modalities": {"output_modalities": ["text"]}},
            {"id": "old-text", "status": "Shutdown", "modalities": {"output_modalities": ["text"]}},
            {"id": "video", "status": "", "modalities": {"output_modalities": ["video"]}},
            {"id": "router", "status": "", "domain": "Router", "modalities": {"output_modalities": ["text"]}},
            {"id": "no-modalities", "status": ""},
        ]
        with patch.object(type(self.coding), 'fetch_catalog', return_value=rows):
            self.assertEqual(self.coding.fetch_models(), ['live-text'])

    def test_unreadable_catalog_falls_back_to_manual_entry(self):
        with patch.object(type(self.coding), 'fetch_catalog', return_value=None):
            self.assertIsNone(self.coding.fetch_models())

    def test_catalog_url_follows_a_custom_base_url(self):
        self.assertEqual(
            self.coding._catalog_url('https://proxy.internal/v1'), 'https://proxy.internal/v1/models')
        self.assertEqual(self.coding._catalog_url(None), self.coding.base_url + '/models')

    def test_documented_endpoints_and_repository(self):
        readme = (ROOT / 'README.md').read_text()
        for profile in self.profiles.values():
            self.assertIn(profile.name, readme)
            self.assertIn(profile.base_url, readme)
            self.assertIn(profile.env_vars[0], readme)
        self.assertIn('infinmalum/hermes-ark-plan-plugin', readme)
        self.assertNotIn('infinmalum/hermes-ark-agentplan-plugin', readme)
        self.assertIn('name: ark-plan', (ROOT / 'plugin.yaml').read_text())


if __name__ == '__main__':
    unittest.main()
