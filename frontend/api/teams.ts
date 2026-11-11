/** Team requests. Each call returns the response data or throws the API's error message. */
import { client, unwrap, type Team, type TeamPatch } from "./client";

const team = (teamId: number) => ({ params: { path: { team_id: teamId } } });

export const teamApi = {
  all: async (): Promise<Team[]> => unwrap(await client.GET("/api/teams")),

  get: async (teamId: number): Promise<Team> => unwrap(await client.GET("/api/teams/{team_id}", team(teamId))),

  create: async (name: string): Promise<Team> => unwrap(await client.POST("/api/teams", { body: { name } })),

  /** Rename and/or set the sprint schedule (`sprintStart` + `sprintWeeks`, both or neither). */
  update: async (teamId: number, patch: TeamPatch): Promise<Team> =>
    unwrap(await client.PATCH("/api/teams/{team_id}", { ...team(teamId), body: patch })),

  /** Deletes the team. What was assigned to it is kept, without a team. */
  remove: async (teamId: number): Promise<void> => {
    unwrap(await client.DELETE("/api/teams/{team_id}", team(teamId)));
  },
};
