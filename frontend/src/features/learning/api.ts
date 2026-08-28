import { api } from "@/lib/api";

export interface Course {
  id: number;
  title: string;
  description: string | null;
  archived: boolean;
  created_at: string;
  lesson_count: number;
  lessons_completed: number;
  progress: number;
  flashcards_due: number;
}

export interface Lesson {
  id: number;
  course_id: number;
  title: string;
  content: string | null;
  position: number;
  completed: boolean;
  completed_on: string | null;
}

export interface CourseDetail extends Course {
  lessons: Lesson[];
}

export interface Flashcard {
  id: number;
  course_id: number;
  front: string;
  back: string;
  ease_factor: number;
  interval_days: number;
  repetitions: number;
  due_on: string;
  last_reviewed_on: string | null;
}

export interface Note {
  id: number;
  course_id: number;
  lesson_id: number | null;
  body: string;
  created_at: string;
}

const BASE = "/learning";

export async function listCourses(): Promise<Course[]> {
  return (await api.get<Course[]>(`${BASE}/courses`)).data;
}

export async function createCourse(input: {
  title: string;
  description?: string | null;
}): Promise<CourseDetail> {
  return (await api.post<CourseDetail>(`${BASE}/courses`, input)).data;
}

export async function getCourse(courseId: number): Promise<CourseDetail> {
  return (await api.get<CourseDetail>(`${BASE}/courses/${courseId}`)).data;
}

export async function updateCourse(
  courseId: number,
  input: { title?: string; description?: string | null; archived?: boolean },
): Promise<CourseDetail> {
  return (await api.patch<CourseDetail>(`${BASE}/courses/${courseId}`, input)).data;
}

export async function deleteCourse(courseId: number): Promise<void> {
  await api.delete(`${BASE}/courses/${courseId}`);
}

export async function addLesson(courseId: number, title: string): Promise<Lesson> {
  return (await api.post<Lesson>(`${BASE}/courses/${courseId}/lessons`, { title })).data;
}

export async function updateLesson(
  lessonId: number,
  input: { title?: string; content?: string | null; completed?: boolean },
): Promise<Lesson> {
  return (await api.patch<Lesson>(`${BASE}/lessons/${lessonId}`, input)).data;
}

export async function deleteLesson(lessonId: number): Promise<void> {
  await api.delete(`${BASE}/lessons/${lessonId}`);
}

export async function listFlashcards(courseId: number): Promise<Flashcard[]> {
  return (await api.get<Flashcard[]>(`${BASE}/courses/${courseId}/flashcards`)).data;
}

export async function addFlashcard(
  courseId: number,
  input: { front: string; back: string },
): Promise<Flashcard> {
  return (await api.post<Flashcard>(`${BASE}/courses/${courseId}/flashcards`, input)).data;
}

export async function deleteFlashcard(flashcardId: number): Promise<void> {
  await api.delete(`${BASE}/flashcards/${flashcardId}`);
}

export async function reviewQueue(courseId?: number): Promise<Flashcard[]> {
  return (await api.get<Flashcard[]>(`${BASE}/review`, { params: { course_id: courseId } })).data;
}

export async function reviewFlashcard(
  flashcardId: number,
  quality: number,
): Promise<Flashcard> {
  return (
    await api.post<Flashcard>(`${BASE}/flashcards/${flashcardId}/review`, { quality })
  ).data;
}

export async function listNotes(courseId: number): Promise<Note[]> {
  return (await api.get<Note[]>(`${BASE}/courses/${courseId}/notes`)).data;
}

export async function addNote(courseId: number, body: string): Promise<Note> {
  return (await api.post<Note>(`${BASE}/courses/${courseId}/notes`, { body })).data;
}

export async function deleteNote(noteId: number): Promise<void> {
  await api.delete(`${BASE}/notes/${noteId}`);
}
