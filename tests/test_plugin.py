import dataclasses
import pathlib
import runpy
import sys
import types
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]


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


class PluginTests(unittest.TestCase):
    def setUp(self):
        profiles = []
        registry = types.ModuleType('providers')
        setattr(registry, "register_provider", profiles.append)
        base = types.ModuleType('providers.base')
        setattr(base, "ProviderProfile", Profile)
        with patch.dict(sys.modules, {'providers': registry, 'providers.base': base}):
            runpy.run_path(str(ROOT / '__init__.py'))
        self.profiles = {p.name: p for p in profiles}

    def test_only_openai_profiles(self):
        self.assertEqual(set(self.profiles), {'ark-agentplan', 'ark-coding-plan'})
        self.assertTrue(all(p.api_mode in ('codex_responses', 'chat_completions') for p in self.profiles.values()))

    def test_agent_backward_compatibility(self):
        p = self.profiles['ark-agentplan']
        self.assertIn('ark-plan', p.aliases)
        self.assertEqual(p.api_mode, 'codex_responses')
        self.assertEqual(p.env_vars, ('ARK_PLAN_API_KEY',))
        self.assertEqual(p.base_url, 'https://ark.cn-beijing.volces.com/api/plan/v3')

    def test_coding_transports_and_credentials(self):
        for name, mode, suffix in [('ark-coding-plan', 'chat_completions', '/api/coding/v3')]:
            p = self.profiles[name]
            self.assertEqual(p.api_mode, mode)
            self.assertEqual(p.base_url, 'https://ark.cn-beijing.volces.com' + suffix)
            self.assertEqual(p.env_vars, ('ARK_CODING_API_KEY',))

    def test_no_alias_collisions_or_catalog_probes(self):
        aliases = [a for p in self.profiles.values() for a in (p.name,) + p.aliases]
        self.assertEqual(len(aliases), len(set(aliases)))
        for p in self.profiles.values():
            self.assertFalse(p.supports_model_listing)
            self.assertFalse(p.supports_health_check)
            self.assertEqual(p.fetch_models(), list(p.fallback_models))
            expected = ('glm-5.3', 'glm-5.3-flash', 'doubao-seed-2.1-lite', 'doubao-seed-2.0-mini')
            if p.name.startswith('ark-coding'):
                expected += ('deepseek-v4-pro', 'deepseek-v4.1-flash')
            self.assertEqual(p.fallback_models, expected)

    def test_documented_endpoints_and_repository(self):
        readme = (ROOT / 'README.md').read_text()
        for p in self.profiles.values():
            self.assertIn(p.name, readme)
            self.assertIn(p.base_url, readme)
            self.assertIn(p.env_vars[0], readme)
        self.assertIn('infinmalum/hermes-ark-plan-plugin', readme)
        self.assertNotIn('infinmalum/hermes-ark-agentplan-plugin', readme)
        self.assertIn('name: ark-plan', (ROOT / 'plugin.yaml').read_text())


if __name__ == '__main__':
    unittest.main()
