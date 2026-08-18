#!/usr/bin/env python3
"""FDE Template CLI Tool"""

import click
import yaml
import subprocess
import os
from pathlib import Path
import structlog

logger = structlog.get_logger()

@click.group()
def cli():
    """FDE Template Command Line Interface"""
    pass

@cli.command()
@click.option('--profile', default='rag-basic', help='Profile name')
@click.argument('project_name')
def init(project_name, profile):
    """Initialize new FDE project"""
    logger.info("init_project", name=project_name, profile=profile)

    project_dir = Path(project_name)
    project_dir.mkdir(exist_ok=True)
    (project_dir / "projects" / project_name).mkdir(parents=True, exist_ok=True)

    config = {
        "project": {"name": project_name},
        "profile": profile,
        "ui": {"enabled": True, "type": "gradio"},
        "database": {"relational": {"enabled": True, "engine": "postgresql"}},
        "storage": {"enabled": True, "engine": "minio"},
        "search": {"enabled": profile != "rag-basic"},
        "graph": {"enabled": False},
        "agent": {"enabled": False},
    }

    with open(project_dir / "project.yaml", "w") as f:
        yaml.dump(config, f)

    click.echo(f"✓ Project '{project_name}' initialized with profile '{profile}'")

@cli.command()
def up():
    """Start containers"""
    logger.info("container_up")
    result = subprocess.run(
        ["docker", "compose", "-f", "infra/docker-compose.yml", "up", "-d"],
        cwd=os.getcwd()
    )
    if result.returncode == 0:
        click.echo("✓ Containers started")
    else:
        click.echo("✗ Failed to start containers")

@cli.command()
def down():
    """Stop containers"""
    logger.info("container_down")
    result = subprocess.run(
        ["docker", "compose", "-f", "infra/docker-compose.yml", "down"],
        cwd=os.getcwd()
    )
    if result.returncode == 0:
        click.echo("✓ Containers stopped")
    else:
        click.echo("✗ Failed to stop containers")

@cli.command()
def validate():
    """Validate project configuration"""
    logger.info("validate")
    if Path("project.yaml").exists():
        with open("project.yaml") as f:
            config = yaml.safe_load(f)
        click.echo(f"✓ Project '{config['project']['name']}' is valid")
    else:
        click.echo("✗ project.yaml not found")

@cli.command()
@click.option('--region', default='ap-northeast-1')
def deploy(region):
    """Deploy to AWS"""
    logger.info("deploy_aws", region=region)
    result = subprocess.run(
        ["cdk", "deploy", "--require-approval=never"],
        cwd="cdk"
    )
    if result.returncode == 0:
        click.echo(f"✓ Deployed to AWS ({region})")
    else:
        click.echo("✗ Deployment failed")

if __name__ == "__main__":
    cli()
