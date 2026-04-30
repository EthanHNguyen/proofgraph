from typer.testing import CliRunner
from proofgraph.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ['--help'])
    assert result.exit_code == 0
    assert 'ProofGraph' in result.output


def test_profiles_list_cli():
    result = runner.invoke(app, ['profiles', 'list'])
    assert result.exit_code == 0
    assert 'starter-security-profile' in result.output


def test_full_map_cli(tmp_path):
    result = runner.invoke(app, ['map', '--profile', 'starter', '--repo', 'examples/sample-repo', '--out', str(tmp_path), '--provider', 'offline'])
    assert result.exit_code == 0, result.output
    assert (tmp_path / 'control-map.json').exists()
