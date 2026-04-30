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


def test_map_accepts_repo_argument(tmp_path):
    result = runner.invoke(app, ['map', 'examples/sample-repo', '--out', str(tmp_path), '--provider', 'offline'])
    assert result.exit_code == 0, result.output
    assert 'proofgraph explain AU-6' in result.output
    assert (tmp_path / 'control-map.json').exists()


def test_run_command_maps_and_validates(tmp_path):
    result = runner.invoke(app, ['run', 'examples/sample-repo', '--out', str(tmp_path), '--provider', 'offline'])
    assert result.exit_code == 0, result.output
    assert 'Validated graph' in result.output
    assert (tmp_path / 'control-map.json').exists()


def test_demo_command_uses_sample_repo(tmp_path):
    result = runner.invoke(app, ['demo', '--out', str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert 'ProofGraph demo complete' in result.output
    assert (tmp_path / 'control-map.json').exists()


def test_run_rejects_missing_target(tmp_path):
    result = runner.invoke(app, ['run', str(tmp_path / 'missing'), '--out', str(tmp_path / 'out'), '--provider', 'offline'])
    assert result.exit_code != 0
    assert 'target path does not exist' in result.output
