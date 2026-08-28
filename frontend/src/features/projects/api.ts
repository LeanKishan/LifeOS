import { api } from "@/lib/api";

export type TaskPriority = "low" | "medium" | "high" | "urgent";

export interface Label {
  id: number;
  name: string;
  color: string;
}

export interface Subtask {
  id: number;
  task_id: number;
  title: string;
  done: boolean;
  position: number;
}

export interface TaskComment {
  id: number;
  task_id: number;
  body: string;
  created_at: string;
}

export interface TaskCard {
  id: number;
  column_id: number;
  title: string;
  priority: TaskPriority;
  due_on: string | null;
  position: number;
  done: boolean;
  completed_at: string | null;
  labels: Label[];
  subtask_total: number;
  subtask_done: number;
  comment_count: number;
}

export interface TaskDetail extends TaskCard {
  project_id: number;
  description: string | null;
  subtasks: Subtask[];
  comments: TaskComment[];
  created_at: string;
  updated_at: string;
}

export interface BoardColumn {
  id: number;
  project_id: number;
  name: string;
  position: number;
  tasks: TaskCard[];
}

export interface Board {
  id: number;
  name: string;
  description: string | null;
  archived: boolean;
  columns: BoardColumn[];
  labels: Label[];
}

export interface ProjectSummary {
  id: number;
  name: string;
  description: string | null;
  archived: boolean;
  created_at: string;
  task_count: number;
}

const BASE = "/projects";

export async function listProjects(archived = false): Promise<ProjectSummary[]> {
  const { data } = await api.get<ProjectSummary[]>(BASE, { params: { archived } });
  return data;
}

export async function createProject(input: {
  name: string;
  description?: string | null;
}): Promise<Board> {
  const { data } = await api.post<Board>(BASE, input);
  return data;
}

export async function getBoard(projectId: number): Promise<Board> {
  const { data } = await api.get<Board>(`${BASE}/${projectId}`);
  return data;
}

export async function updateProject(
  projectId: number,
  input: { name?: string; description?: string | null; archived?: boolean },
): Promise<Board> {
  const { data } = await api.patch<Board>(`${BASE}/${projectId}`, input);
  return data;
}

export async function deleteProject(projectId: number): Promise<void> {
  await api.delete(`${BASE}/${projectId}`);
}

export async function addColumn(projectId: number, name: string): Promise<void> {
  await api.post(`${BASE}/${projectId}/columns`, { name });
}

export async function moveColumn(columnId: number, position: number): Promise<void> {
  await api.post(`${BASE}/columns/${columnId}/move`, { position });
}

export async function renameColumn(columnId: number, name: string): Promise<void> {
  await api.patch(`${BASE}/columns/${columnId}`, { name });
}

export async function deleteColumn(columnId: number): Promise<void> {
  await api.delete(`${BASE}/columns/${columnId}`);
}

export async function createTask(
  projectId: number,
  input: { column_id: number; title: string; priority?: TaskPriority },
): Promise<TaskDetail> {
  const { data } = await api.post<TaskDetail>(`${BASE}/${projectId}/tasks`, input);
  return data;
}

export async function getTask(taskId: number): Promise<TaskDetail> {
  const { data } = await api.get<TaskDetail>(`${BASE}/tasks/${taskId}`);
  return data;
}

export async function updateTask(
  taskId: number,
  input: {
    title?: string;
    description?: string | null;
    priority?: TaskPriority;
    due_on?: string | null;
    done?: boolean;
  },
): Promise<TaskDetail> {
  const { data } = await api.patch<TaskDetail>(`${BASE}/tasks/${taskId}`, input);
  return data;
}

export async function moveTask(
  taskId: number,
  columnId: number,
  position: number,
): Promise<TaskDetail> {
  const { data } = await api.post<TaskDetail>(`${BASE}/tasks/${taskId}/move`, {
    column_id: columnId,
    position,
  });
  return data;
}

export async function deleteTask(taskId: number): Promise<void> {
  await api.delete(`${BASE}/tasks/${taskId}`);
}

export async function setTaskLabels(taskId: number, labelIds: number[]): Promise<TaskDetail> {
  const { data } = await api.put<TaskDetail>(`${BASE}/tasks/${taskId}/labels`, {
    label_ids: labelIds,
  });
  return data;
}

export async function addSubtask(taskId: number, title: string): Promise<void> {
  await api.post(`${BASE}/tasks/${taskId}/subtasks`, { title });
}

export async function updateSubtask(
  subtaskId: number,
  input: { title?: string; done?: boolean },
): Promise<void> {
  await api.patch(`${BASE}/subtasks/${subtaskId}`, input);
}

export async function deleteSubtask(subtaskId: number): Promise<void> {
  await api.delete(`${BASE}/subtasks/${subtaskId}`);
}

export async function addLabel(
  projectId: number,
  input: { name: string; color?: string },
): Promise<Label> {
  const { data } = await api.post<Label>(`${BASE}/${projectId}/labels`, input);
  return data;
}

export async function deleteLabel(labelId: number): Promise<void> {
  await api.delete(`${BASE}/labels/${labelId}`);
}

export async function addComment(taskId: number, body: string): Promise<void> {
  await api.post(`${BASE}/tasks/${taskId}/comments`, { body });
}

export async function deleteComment(commentId: number): Promise<void> {
  await api.delete(`${BASE}/comments/${commentId}`);
}
