/** Project requests. Each call returns the response data or throws the API's error message. */
import { client, unwrap, type Project, type ProjectPatch } from "./client";

const project = (projectId: number) => ({ params: { path: { project_id: projectId } } });

export const projectApi = {
  /** A team's projects, active first. */
  forTeam: async (teamId: number): Promise<Project[]> =>
    unwrap(await client.GET("/api/teams/{team_id}/projects", { params: { path: { team_id: teamId } } })),

  /** Projects without a team (e.g. after their team was deleted). */
  teamless: async (): Promise<Project[]> => unwrap(await client.GET("/api/projects/teamless")),

  get: async (projectId: number): Promise<Project> => unwrap(await client.GET("/api/projects/{project_id}", project(projectId))),

  create: async (teamId: number, name: string): Promise<Project> =>
    unwrap(await client.POST("/api/teams/{team_id}/projects", { params: { path: { team_id: teamId } }, body: { name, description: "" } })),

  update: async (projectId: number, patch: ProjectPatch): Promise<Project> =>
    unwrap(await client.PATCH("/api/projects/{project_id}", { ...project(projectId), body: patch })),

  /** Deletes the project and all of its todo lists (daily lists included). */
  remove: async (projectId: number): Promise<void> => {
    unwrap(await client.DELETE("/api/projects/{project_id}", project(projectId)));
  },
};
