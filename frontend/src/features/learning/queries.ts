import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as ln from "@/features/learning/api";

const KEY = ["learning"] as const;

export function useCourses() {
  return useQuery({ queryKey: [...KEY, "courses"], queryFn: ln.listCourses });
}

export function useCourse(courseId: number) {
  return useQuery({
    queryKey: [...KEY, "course", courseId],
    queryFn: () => ln.getCourse(courseId),
    enabled: Number.isFinite(courseId) && courseId > 0,
  });
}

export function useFlashcards(courseId: number) {
  return useQuery({
    queryKey: [...KEY, "flashcards", courseId],
    queryFn: () => ln.listFlashcards(courseId),
    enabled: courseId > 0,
  });
}

export function useNotes(courseId: number) {
  return useQuery({
    queryKey: [...KEY, "notes", courseId],
    queryFn: () => ln.listNotes(courseId),
    enabled: courseId > 0,
  });
}

export function useReviewCount() {
  return useQuery({
    queryKey: [...KEY, "review-count"],
    queryFn: () => ln.reviewQueue(),
  });
}

export function useLearningMutation<TArgs, TResult>(fn: (args: TArgs) => Promise<TResult>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
