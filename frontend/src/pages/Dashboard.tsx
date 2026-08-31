import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AxiosError } from 'axios';
import { Button } from '../components';
import { User } from '../api/authAPI';
import lmsAPI, { Assignment, Course, Doubt, Submission } from '../api/lmsAPI';
import styles from './Dashboard.module.css';

const errorText = (error: unknown) => (error as AxiosError<{ detail?: string }>).response?.data?.detail || 'Request failed. Please try again.';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || 'null') as User | null;
  const isTutor = user?.role === 'tutor';
  const [courses, setCourses] = useState<Course[]>([]);
  const [enrolledCourses, setEnrolledCourses] = useState<Course[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [students, setStudents] = useState<{ id: number; name: string; email: string }[]>([]);
  const [doubtText, setDoubtText] = useState('');
  const [doubtHistory, setDoubtHistory] = useState<Doubt[]>([]);
  const [latestAnswer, setLatestAnswer] = useState<Doubt | null>(null);
  const [message, setMessage] = useState('');
  const [courseForm, setCourseForm] = useState({ title: '', description: '' });
  const [assignmentForm, setAssignmentForm] = useState({ title: '', description: '', due_date: '' });

  const loadCourseDoubts = async (courseId: number) => {
    try {
      const doubts = await lmsAPI.listCourseDoubts(courseId);
      setDoubtHistory(doubts);
      setLatestAnswer(doubts[0] ?? null);
    } catch (error) {
      setMessage(errorText(error));
    }
  };

  const loadCourses = async () => { try { setCourses(await lmsAPI.listCourses()); if (!isTutor) setEnrolledCourses(await lmsAPI.listEnrolledCourses()); } catch (error) { setMessage(errorText(error)); } };
  const loadCourseWork = async (course: Course) => { setSelectedCourse(course); try { setAssignments(await lmsAPI.listAssignments(course.id)); setSubmissions(await lmsAPI.listSubmissions(course.id)); if (isTutor) setStudents(await lmsAPI.listStudents(course.id)); else await loadCourseDoubts(course.id); } catch (error) { setMessage(errorText(error)); } };
  useEffect(() => { if (!user) navigate('/login'); else loadCourses(); }, []);
  const logout = () => { localStorage.clear(); navigate('/login'); };
  const createCourse = async (event: React.FormEvent) => { event.preventDefault(); try { await lmsAPI.createCourse(courseForm); setCourseForm({ title: '', description: '' }); setMessage('Course created.'); loadCourses(); } catch (error) { setMessage(errorText(error)); } };
  const enroll = async (course: Course) => { try { await lmsAPI.enroll(course.id); setMessage(`Enrolled in ${course.title}.`); loadCourses(); } catch (error) { setMessage(errorText(error)); } };
  const createAssignment = async (event: React.FormEvent) => { event.preventDefault(); if (!selectedCourse) return; try { await lmsAPI.createAssignment(selectedCourse.id, assignmentForm); setAssignmentForm({ title: '', description: '', due_date: '' }); await loadCourseWork(selectedCourse); } catch (error) { setMessage(errorText(error)); } };
  const submit = async (assignmentId: number, fileUrl: string) => { try { await lmsAPI.submit(assignmentId, fileUrl); setMessage('Work submitted.'); if (selectedCourse) await loadCourseWork(selectedCourse); } catch (error) { setMessage(errorText(error)); } };
  const grade = async (submission: Submission) => { const value = window.prompt('Grade (0-100)', String(submission.grade ?? '')); if (value === null) return; try { await lmsAPI.grade(submission.id, Number(value), window.prompt('Feedback', submission.feedback || '') || ''); if (selectedCourse) await loadCourseWork(selectedCourse); } catch (error) { setMessage(errorText(error)); } };
  const upload = async (event: React.ChangeEvent<HTMLInputElement>) => { const file = event.target.files?.[0]; if (!file || !selectedCourse) return; try { await lmsAPI.uploadMaterial(selectedCourse.id, file); setMessage('Material uploaded and indexed.'); } catch (error) { setMessage(errorText(error)); } };
  const askDoubt = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedCourse || !doubtText.trim()) return;
    try {
      const response = await lmsAPI.askDoubt(selectedCourse.id, { text_content: doubtText.trim() });
      setDoubtText('');
      setLatestAnswer(response);
      setMessage(response.source === 'matched' ? 'Instant match found for your doubt.' : 'New answer generated for your doubt.');
      await loadCourseDoubts(selectedCourse.id);
    } catch (error) {
      setMessage(errorText(error));
    }
  };
  if (!user) return null;
  return <div className={styles.container}>
    <header className={styles.header}><div className={styles.headerContent}><div><span className={styles.kicker}>TUTOR LMS</span><h1>{isTutor ? 'Your teaching studio' : 'Your learning desk'}</h1></div><Button variant="secondary" onClick={logout}>Log out</Button></div></header>
    <main className={styles.main}><div className={styles.intro}><p className={styles.eyebrow}>{isTutor ? 'TUTOR CONSOLE' : 'STUDENT CONSOLE'}</p><h2>Good to see you, {user.name.split(' ')[0]}.</h2><p>{isTutor ? 'Shape focused courses, publish work, and give useful feedback.' : 'Find your next course, keep up with deadlines, and see your progress.'}</p></div>
      {message && <div className={styles.notice}>{message}</div>}
      {isTutor && <section className={styles.formPanel}><h3>Create a course</h3><form onSubmit={createCourse} className={styles.form}><input required placeholder="Course title" value={courseForm.title} onChange={e => setCourseForm({ ...courseForm, title: e.target.value })} /><textarea required placeholder="What will students learn?" value={courseForm.description} onChange={e => setCourseForm({ ...courseForm, description: e.target.value })} /><Button type="submit">Create course</Button></form></section>}
      <section><div className={styles.sectionHeader}><div><p className={styles.eyebrow}>{isTutor ? 'YOUR CATALOG' : 'DISCOVER'}</p><h3>{isTutor ? 'Courses you lead' : 'Courses ready to join'}</h3></div><span className={styles.count}>{courses.length} courses</span></div><div className={styles.courseGrid}>{courses.map(course => <article className={styles.course} key={course.id}><span className={styles.courseMark}>{String(course.id).padStart(2, '0')}</span><h4>{course.title}</h4><p>{course.description}</p><small>{course.enrolled_count} enrolled</small><div className={styles.actions}>{isTutor ? <Button variant="secondary" onClick={() => loadCourseWork(course)}>Open studio</Button> : <Button onClick={() => enroll(course)}>Enroll</Button>}</div></article>)}</div></section>
      {!isTutor && <section className={styles.enrolled}><div className={styles.sectionHeader}><div><p className={styles.eyebrow}>YOUR LEARNING</p><h3>Enrolled courses</h3></div><span className={styles.count}>{enrolledCourses.length} courses</span></div><div className={styles.courseGrid}>{enrolledCourses.map(course => <article className={styles.course} key={course.id}><span className={styles.courseMark}>ACTIVE</span><h4>{course.title}</h4><p>{course.description}</p><div className={styles.actions}><Button variant="secondary" onClick={() => loadCourseWork(course)}>View assignments</Button></div></article>)}</div></section>}
      {selectedCourse && <section className={styles.workspace}><div className={styles.sectionHeader}><div><p className={styles.eyebrow}>COURSE WORKSPACE</p><h3>{selectedCourse.title}</h3></div><span className={styles.count}>{assignments.length} assignments</span></div><div className={styles.workspaceGrid}><div><h4>Assignments</h4>{assignments.map(assignment => <div className={styles.assignment} key={assignment.id}><strong>{assignment.title}</strong><span>{assignment.description}</span><small>Due {new Date(assignment.due_date).toLocaleDateString()}</small>{!isTutor && <form onSubmit={e => { e.preventDefault(); submit(assignment.id, (e.currentTarget.elements.namedItem('fileUrl') as HTMLInputElement).value); }} className={styles.inlineForm}><input name="fileUrl" required placeholder="Link to your work" /><Button type="submit">Submit</Button></form>}</div>)}</div><div><h4>{isTutor ? 'Publish and review' : 'Your grades'}</h4>{isTutor ? <><form onSubmit={createAssignment} className={styles.form}><input required placeholder="Assignment title" value={assignmentForm.title} onChange={e => setAssignmentForm({ ...assignmentForm, title: e.target.value })} /><textarea required placeholder="Brief and requirements" value={assignmentForm.description} onChange={e => setAssignmentForm({ ...assignmentForm, description: e.target.value })} /><input required type="datetime-local" value={assignmentForm.due_date} onChange={e => setAssignmentForm({ ...assignmentForm, due_date: e.target.value })} /><Button type="submit">Publish assignment</Button></form><label className={styles.upload}>Upload PDF material<input type="file" accept="application/pdf" onChange={upload} /></label><h4 className={styles.rosterTitle}>Enrolled students</h4>{students.map(student => <div className={styles.roster} key={student.id}>{student.name}<small>{student.email}</small></div>)}</> : submissions.map(submission => <div className={styles.assignment} key={submission.id}><strong>Assignment #{submission.assignment_id}</strong><span>{submission.file_url}</span><small>{submission.grade === null ? 'Awaiting review' : `Grade: ${submission.grade}/100`}{submission.feedback ? ` · ${submission.feedback}` : ''}</small></div>)}</div></div>{isTutor && <div className={styles.review}><h4>Submissions</h4>{submissions.map(submission => <div className={styles.reviewRow} key={submission.id}><span>Student #{submission.student_id} · {submission.file_url}</span><Button variant="secondary" onClick={() => grade(submission)}>Grade</Button></div>)}</div>}</section>}
      {!isTutor && selectedCourse && (
        <section className={styles.doubtPanel}>
          <div className={styles.sectionHeader}>
            <div>
              <p className={styles.eyebrow}>DOUBT MATCHING</p>
              <h3>Ask a question</h3>
            </div>
          </div>

          <form onSubmit={askDoubt} className={styles.doubtForm}>
            <textarea required placeholder="Ask a course-related question..." value={doubtText} onChange={e => setDoubtText(e.target.value)} />
            <Button type="submit" disabled={!doubtText.trim()}>Submit doubt</Button>
          </form>

          {latestAnswer && latestAnswer.answer ? (
            <div className={styles.answerCard}>
              <span className={`${styles.badge} ${latestAnswer.source === 'matched' ? styles.instant : styles.generated}`}>
                {latestAnswer.source === 'matched' ? 'instant match' : 'freshly generated'}
              </span>
              <h4>Answer</h4>
              <p>{latestAnswer.answer.content}</p>
            </div>
          ) : null}

          <div className={styles.historyList}>
            <h4>Recent doubts</h4>
            {doubtHistory.length === 0 ? (
              <p className={styles.emptyState}>No doubts yet for this course.</p>
            ) : (
              doubtHistory.map(doubt => (
                <article key={doubt.id} className={styles.doubtItem}>
                  <div className={styles.doubtMeta}>
                    <strong>{new Date(doubt.created_at).toLocaleDateString()}</strong>
                    <span className={`${styles.badge} ${doubt.source === 'matched' ? styles.instant : styles.generated}`}>
                      {doubt.source === 'matched' ? 'instant match' : 'freshly generated'}
                    </span>
                  </div>
                  <p className={styles.doubtPrompt}>{doubt.text_content}</p>
                  {doubt.answer ? (
                    <div className={styles.answerBox}>
                      <strong>Answer</strong>
                      <p>{doubt.answer.content}</p>
                    </div>
                  ) : (
                    <p className={styles.emptyState}>Awaiting answer…</p>
                  )}
                </article>
              ))
            )}
          </div>
        </section>
      )}
    </main></div>;
};
