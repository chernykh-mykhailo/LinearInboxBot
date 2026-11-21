import logging
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)

LINEAR_GRAPHQL_ENDPOINT = "https://api.linear.app/graphql"


class LinearClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        self._cached_teams: List[Dict[str, Any]] = []
        self._cached_projects: List[Dict[str, Any]] = []

    async def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                LINEAR_GRAPHQL_ENDPOINT,
                headers=self.headers,
                json={"query": query, "variables": variables or {}},
            )
            response.raise_for_status()
            data = response.json()
            if "errors" in data and data["errors"]:
                logger.error(f"Linear GraphQL error: {data['errors']}")
                raise RuntimeError(data["errors"][0].get("message", "Unknown GraphQL error"))
            return data.get("data", {})

    async def refresh_workspace_data(self) -> None:
        """Fetches and caches all teams and active projects."""
        query = """
        query GetTeamsAndProjects {
          teams {
            nodes {
              id
              name
              key
            }
          }
          projects(filter: { state: { in: ["planned", "started"] } }) {
            nodes {
              id
              name
              icon
              color
              teams {
                nodes {
                  id
                  key
                }
              }
            }
          }
        }
        """
        data = await self.execute_query(query)
        self._cached_teams = data.get("teams", {}).get("nodes", [])
        self._cached_projects = data.get("projects", {}).get("nodes", [])
        logger.info(f"Loaded {len(self._cached_teams)} teams and {len(self._cached_projects)} projects from Linear.")

    def get_teams(self) -> List[Dict[str, Any]]:
        return self._cached_teams

    def get_projects(self) -> List[Dict[str, Any]]:
        return self._cached_projects

    def get_default_team_id(self) -> Optional[str]:
        if self._cached_teams:
            return self._cached_teams[0]["id"]
        return None

    async def create_issue(
        self,
        title: str,
        description: Optional[str] = None,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Creates a new issue in Linear."""
        if not team_id:
            team_id = self.get_default_team_id()

        if not team_id:
            raise ValueError("No team found in your Linear workspace. Please create a team first.")

        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue {
              id
              identifier
              title
              url
              project {
                id
                name
              }
            }
          }
        }
        """
        issue_input: Dict[str, Any] = {
            "title": title,
            "teamId": team_id,
        }
        if description:
            issue_input["description"] = description
        if project_id:
            issue_input["projectId"] = project_id
        if priority is not None and priority in (0, 1, 2, 3, 4):
            issue_input["priority"] = priority

        data = await self.execute_query(mutation, {"input": issue_input})
        result = data.get("issueCreate", {})
        if not result.get("success"):
            raise RuntimeError("Linear failed to create the issue.")
        return result.get("issue", {})
