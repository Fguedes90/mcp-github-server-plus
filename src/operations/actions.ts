import { z } from "zod";
import { githubRequest } from "../common/utils.js";

export const TriggerWorkflowOptionsSchema = z.object({
  owner: z.string(),
  repo: z.string(),
  workflow_id: z.union([z.string(), z.number()]),
  ref: z.string(),
  inputs: z.record(z.any()).optional()
});

/**
 * Triggers a GitHub Actions workflow dispatch event.
 */
export async function triggerWorkflow(params: z.TypeOf<typeof TriggerWorkflowOptionsSchema>): Promise<void> {
  const { owner, repo, workflow_id, ref, inputs } = TriggerWorkflowOptionsSchema.parse(params);
  await githubRequest(`https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow_id}/dispatches`, {
    method: "POST",
    body: { ref, inputs }
  });
}

/**
 * Lists all workflows for a repository.
 */
export async function listWorkflows(owner: string, repo: string): Promise<any> {
  const response = await githubRequest(`https://api.github.com/repos/${owner}/${repo}/actions/workflows`);
  return response;
}

/**
 * Gets details of a specific workflow.
 */
export async function getWorkflow(owner: string, repo: string, workflow_id: string | number): Promise<any> {
  const response = await githubRequest(`https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow_id}`);
  return response;
}

/**
 * Lists workflow runs. If workflow_id is provided, lists runs for that workflow; otherwise, lists all runs.
 */
export async function listWorkflowRuns(owner: string, repo: string, workflow_id?: string | number): Promise<any> {
  const endpoint = workflow_id ?
    `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow_id}/runs` :
    `https://api.github.com/repos/${owner}/${repo}/actions/runs`;
  const response = await githubRequest(endpoint);
  return response;
}

/**
 * Debug a failed workflow run by retrieving its logs URL.
 */
export const DebugWorkflowRunSchema = z.object({
  owner: z.string(),
  repo: z.string(),
  run_id: z.union([z.string(), z.number()])
});

export async function debugWorkflowRun(params: z.TypeOf<typeof DebugWorkflowRunSchema>): Promise<{ logs_url: string }> {
  const { owner, repo, run_id } = DebugWorkflowRunSchema.parse(params);
  const workflowRun = await githubRequest(`https://api.github.com/repos/${owner}/${repo}/actions/runs/${run_id}`);
  const runData = workflowRun as { logs_url?: string };
  if (!runData.logs_url) {
    throw new Error("No logs found for this workflow run.");
  }
  return { logs_url: runData.logs_url };
} 