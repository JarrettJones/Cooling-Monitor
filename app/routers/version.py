from fastapi import APIRouter
import subprocess
import os

router = APIRouter(prefix="/api/version", tags=["version"])


@router.get("/")
async def get_version():
    """Get current git branch and commit information"""
    try:
        # Get current branch
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        
        # Get current commit hash (short)
        commit = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        
        # Get commit message
        commit_msg = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=%s'],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        
        return {
            "branch": branch,
            "commit": commit,
            "commit_message": commit_msg
        }
    except Exception as e:
        return {
            "branch": "unknown",
            "commit": "unknown",
            "commit_message": str(e)
        }
