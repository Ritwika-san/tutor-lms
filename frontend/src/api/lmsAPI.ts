import apiClient from './client';

export interface Course { id: number; tutor_id: number; title: string; description: string; created_at: string; enrolled_count: number; }
export interface Assignment { id: number; course_id: number; title: string; description: string; due_date: string; }
export interface Submission { id: number; assignment_id: number; student_id: number; file_url: string; grade: number | null; feedback: string | null; submitted_at: string; }
export interface EnrolledStudent { id: number; name: string; email: string; }
export interface CourseInput { title: string; description: string; }
export interface AssignmentInput { title: string; description: string; due_date: string; }
export interface Answer { id: number; doubt_id: number; content: string; source: 'matched' | 'generated'; like_count: number; created_at: string; }
export interface Doubt { id: number; course_id: number; student_id: number; text_content: string; status: 'pending' | 'answered'; created_at: string; answer: Answer | null; source: 'matched' | 'generated' | null; }
export interface DoubtInput { text_content: string; }

const lmsAPI = {
  listCourses: async () => (await apiClient.get<Course[]>('/courses')).data,
  listEnrolledCourses: async () => (await apiClient.get<Course[]>('/courses/enrolled')).data,
  createCourse: async (data: CourseInput) => (await apiClient.post<Course>('/courses', data)).data,
  enroll: async (courseId: number) => apiClient.post(`/courses/${courseId}/enroll`),
  listAssignments: async (courseId: number) => (await apiClient.get<Assignment[]>(`/courses/${courseId}/assignments`)).data,
  createAssignment: async (courseId: number, data: AssignmentInput) => (await apiClient.post<Assignment>(`/courses/${courseId}/assignments`, data)).data,
  submit: async (assignmentId: number, fileUrl: string) => (await apiClient.post<Submission>(`/assignments/${assignmentId}/submit`, null, { params: { file_url: fileUrl } })).data,
  listSubmissions: async (courseId: number) => (await apiClient.get<Submission[]>(`/courses/${courseId}/submissions`)).data,
  listStudents: async (courseId: number) => (await apiClient.get<EnrolledStudent[]>(`/courses/${courseId}/students`)).data,
  askDoubt: async (courseId: number, data: DoubtInput) => (await apiClient.post<Doubt>(`/courses/${courseId}/doubts`, data)).data,
  listCourseDoubts: async (courseId: number) => (await apiClient.get<Doubt[]>(`/courses/${courseId}/doubts`)).data,
  getDoubt: async (doubtId: number) => (await apiClient.get<Doubt>(`/doubts/${doubtId}`)).data,
  grade: async (submissionId: number, grade: number, feedback: string) => (await apiClient.patch<Submission>(`/submissions/${submissionId}/grade`, { grade, feedback })).data,
  uploadMaterial: async (courseId: number, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return (await apiClient.post(`/courses/${courseId}/materials`, form)).data;
  },
};

export default lmsAPI;
