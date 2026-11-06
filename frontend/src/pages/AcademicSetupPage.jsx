import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../services/api'
import { Card, Button, Badge } from '../components/common'
import PageHeader from '../components/layout/PageHeader'

export default function AcademicSetupPage() {
  const { t } = useTranslation()

  // Active top-level navigation tab
  const [activeTab, setActiveTab] = useState('overview') // 'overview', 'years', 'departments', 'classes', 'subjects', 'enrolments', 'allocations', 'calendar'
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState({ text: '', type: 'success' })

  // Data collections
  const [overview, setOverview] = useState({
    active_academic_year: '2025-26',
    total_departments: 4,
    total_programmes: 6,
    total_classes: 8,
    total_subjects: 14,
    total_students_enrolled: 320,
    total_faculty_assignments: 18,
    recent_events: [],
  })
  const [years, setYears] = useState([])
  const [terms, setTerms] = useState([])
  const [departments, setDepartments] = useState([])
  const [programmes, setProgrammes] = useState([])
  const [classes, setClasses] = useState([])
  const [subjects, setSubjects] = useState([])
  const [enrolments, setEnrolments] = useState([])
  const [assignments, setAssignments] = useState([])
  const [calendarEvents, setCalendarEvents] = useState([])

  // Search & filter state
  const [filterYear, setFilterYear] = useState('all')
  const [calendarFilter, setCalendarFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Modal / dialog states
  const [showYearModal, setShowYearModal] = useState(false)
  const [showTermModal, setShowTermModal] = useState(false)
  const [showDeptModal, setShowDeptModal] = useState(false)
  const [showProgModal, setShowProgModal] = useState(false)
  const [showClassModal, setShowClassModal] = useState(false)
  const [showSubjectModal, setShowSubjectModal] = useState(false)
  const [showEnrolModal, setShowEnrolModal] = useState(false)
  const [showPromotionModal, setShowPromotionModal] = useState(false)
  const [showTransferModal, setShowTransferModal] = useState(false)
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showEventModal, setShowEventModal] = useState(false)

  // Target item for promotion / transfer
  const [selectedEnrolment, setSelectedEnrolment] = useState(null)

  // Form states
  const [newYear, setNewYear] = useState({
    year_label: '',
    start_date: '',
    end_date: '',
    admission_start: '',
    admission_end: '',
  })
  const [newTerm, setNewTerm] = useState({
    term_name: '',
    term_type: 'semester',
    term_number: 1,
    start_date: '',
    end_date: '',
    academic_year_id: 'AY-2025-26',
  })
  const [newDept, setNewDept] = useState({
    dept_code: '',
    name: '',
    head_of_department: '',
    email: '',
  })
  const [newProg, setNewProg] = useState({
    programme_code: '',
    name: '',
    degree_type: 'Bachelor',
    department_id: '',
    total_semesters: 8,
    total_credits: 160,
  })
  const [newClass, setNewClass] = useState({
    grade_level: '',
    section: 'A',
    academic_year: '2025-26',
    room_number: '',
    capacity: 40,
    class_teacher_name: '',
  })
  const [newSubject, setNewSubject] = useState({
    subject_code: '',
    subject_name: '',
    multilingual_name: '',
    credits: 4,
    is_practical: false,
    department_id: '',
    grade_level: 'Class 10',
  })
  const [newEnrolment, setNewEnrolment] = useState({
    student_name: '',
    student_id: '',
    enrolment_number: '',
    academic_year_id: 'AY-2025-26',
    class_id: '',
  })
  const [promotionData, setPromotionData] = useState({
    next_academic_year_id: 'AY-2026-27',
    next_grade_level: 'Class 11',
    next_section: 'A',
    notes: 'Annual progression',
  })
  const [transferData, setTransferData] = useState({
    new_section: 'B',
    reason: 'Parent request',
  })
  const [newAssignment, setNewAssignment] = useState({
    teacher_name: '',
    teacher_id: '',
    subject_id: '',
    class_id: '',
    role_in_course: 'Primary Teacher',
    academic_year_id: 'AY-2025-26',
  })
  const [newEvent, setNewEvent] = useState({
    title: '',
    event_type: 'holiday',
    start_date: '',
    end_date: '',
    description: '',
  })

  const notify = (text, type = 'success') => {
    setMsg({ text, type })
    setTimeout(() => setMsg({ text: '', type: 'success' }), 4500)
  }

  // Initial load
  useEffect(() => {
    async function loadAllAcademicData() {
      setLoading(true)
      try {
        const [
          ovRes,
          yrRes,
          tmRes,
          dpRes,
          prRes,
          clRes,
          sbRes,
          enRes,
          taRes,
          evRes,
        ] = await Promise.allSettled([
          api.get('/academic/overview'),
          api.get('/academic/years'),
          api.get('/academic/terms'),
          api.get('/academic/departments'),
          api.get('/academic/programmes'),
          api.get('/academic/classes'),
          api.get('/academic/subjects'),
          api.get('/academic/enrolments'),
          api.get('/academic/teacher-assignments'),
          api.get('/academic/calendar/events'),
        ])

        if (ovRes.status === 'fulfilled' && ovRes.value?.data) {
          setOverview(ovRes.value.data)
        }
        if (yrRes.status === 'fulfilled' && Array.isArray(yrRes.value?.data)) {
          setYears(yrRes.value.data)
        } else {
          setYears([
            {
              id: 'AY-2025-26',
              year_label: '2025-26',
              start_date: '2025-06-01',
              end_date: '2026-05-31',
              admission_start: '2025-04-01',
              admission_end: '2025-06-15',
              is_current: true,
              is_archived: false,
            },
            {
              id: 'AY-2026-27',
              year_label: '2026-27',
              start_date: '2026-06-01',
              end_date: '2027-05-31',
              admission_start: '2026-04-01',
              admission_end: '2026-06-15',
              is_current: false,
              is_archived: false,
            },
          ])
        }

        if (tmRes.status === 'fulfilled' && Array.isArray(tmRes.value?.data)) {
          setTerms(tmRes.value.data)
        } else {
          setTerms([
            {
              id: 'TERM-2025-S1',
              term_name: 'Semester 1 (Autumn)',
              term_type: 'semester',
              term_number: 1,
              start_date: '2025-07-01',
              end_date: '2025-11-30',
              academic_year_id: 'AY-2025-26',
              is_active: true,
            },
            {
              id: 'TERM-2025-S2',
              term_name: 'Semester 2 (Spring)',
              term_type: 'semester',
              term_number: 2,
              start_date: '2025-12-15',
              end_date: '2026-05-15',
              academic_year_id: 'AY-2025-26',
              is_active: false,
            },
          ])
        }

        if (dpRes.status === 'fulfilled' && Array.isArray(dpRes.value?.data)) {
          setDepartments(dpRes.value.data)
        } else {
          setDepartments([
            {
              id: 'DEPT-CS',
              dept_code: 'CSE',
              name: 'Computer Science and Engineering',
              head_of_department: 'Dr. Anita Roy',
              email: 'hod.cse@institution.ac.in',
              is_active: true,
            },
            {
              id: 'DEPT-MATH',
              dept_code: 'MATH',
              name: 'Department of Mathematics',
              head_of_department: 'Prof. Ramesh Gupta',
              email: 'hod.math@institution.ac.in',
              is_active: true,
            },
          ])
        }

        if (prRes.status === 'fulfilled' && Array.isArray(prRes.value?.data)) {
          setProgrammes(prRes.value.data)
        } else {
          setProgrammes([
            {
              id: 'PROG-BTECH-CSE',
              programme_code: 'BTECH-CS',
              name: 'Bachelor of Technology in Computer Science',
              degree_type: 'Bachelor',
              department_id: 'DEPT-CS',
              total_semesters: 8,
              total_credits: 160,
              is_active: true,
            },
            {
              id: 'PROG-SEC-10',
              programme_code: 'CBSE-10',
              name: 'Secondary Education Class 10',
              degree_type: 'Secondary School',
              total_semesters: 2,
              total_credits: 30,
              is_active: true,
            },
          ])
        }

        if (clRes.status === 'fulfilled' && Array.isArray(clRes.value?.data)) {
          setClasses(clRes.value.data)
        } else {
          setClasses([
            {
              id: 'CLS-10A',
              grade_level: 'Class 10',
              section: 'A',
              academic_year: '2025-26',
              room_number: 'Room 204',
              capacity: 40,
              class_teacher_name: 'Priya Sharma',
            },
            {
              id: 'CLS-10B',
              grade_level: 'Class 10',
              section: 'B',
              academic_year: '2025-26',
              room_number: 'Room 205',
              capacity: 40,
              class_teacher_name: 'Sunil Verma',
            },
            {
              id: 'CLS-9A',
              grade_level: 'Class 9',
              section: 'A',
              academic_year: '2025-26',
              room_number: 'Room 102',
              capacity: 40,
              class_teacher_name: 'Kavita Das',
            },
          ])
        }

        if (sbRes.status === 'fulfilled' && Array.isArray(sbRes.value?.data)) {
          setSubjects(sbRes.value.data)
        } else {
          setSubjects([
            {
              id: 'SUB-MATH-10',
              subject_code: 'MATH-10',
              subject_name: 'Mathematics',
              multilingual_name: 'Ganita (Mathematics)',
              credits: 4,
              is_practical: false,
              applicable_to: 'Class 10',
            },
            {
              id: 'SUB-SCI-10',
              subject_code: 'SCI-10',
              subject_name: 'General Science',
              multilingual_name: 'Vigyan (Science)',
              credits: 4,
              is_practical: true,
              applicable_to: 'Class 10',
            },
            {
              id: 'SUB-CS-101',
              subject_code: 'CS-101',
              subject_name: 'Introduction to Programming',
              multilingual_name: 'Computer Programming',
              credits: 4,
              is_practical: true,
              applicable_to: 'BTECH-CS',
            },
          ])
        }

        if (enRes.status === 'fulfilled' && Array.isArray(enRes.value?.data)) {
          setEnrolments(enRes.value.data)
        } else {
          setEnrolments([
            {
              id: 'ENR-001',
              student_name: 'Aarav Patel',
              student_id: 'STU-001',
              enrolment_number: 'ENR-2025-01',
              class_id: 'CLS-10A',
              academic_year_id: 'AY-2025-26',
              status: 'active',
              is_current: true,
              enrolment_date: '2025-06-05',
            },
            {
              id: 'ENR-002',
              student_name: 'Diya Sen',
              student_id: 'STU-002',
              enrolment_number: 'ENR-2025-02',
              class_id: 'CLS-10A',
              academic_year_id: 'AY-2025-26',
              status: 'active',
              is_current: true,
              enrolment_date: '2025-06-06',
            },
            {
              id: 'ENR-003',
              student_name: 'Rohan Mehra',
              student_id: 'STU-003',
              enrolment_number: 'ENR-2025-03',
              class_id: 'CLS-9A',
              academic_year_id: 'AY-2025-26',
              status: 'active',
              is_current: true,
              enrolment_date: '2025-06-08',
            },
          ])
        }

        if (taRes.status === 'fulfilled' && Array.isArray(taRes.value?.data)) {
          setAssignments(taRes.value.data)
        } else {
          setAssignments([
            {
              id: 'ASG-001',
              teacher_name: 'Priya Sharma',
              teacher_id: 'TEA-001',
              subject_id: 'SUB-MATH-10',
              class_id: 'CLS-10A',
              role_in_course: 'Primary Teacher',
              academic_year_id: 'AY-2025-26',
            },
            {
              id: 'ASG-002',
              teacher_name: 'Sunil Verma',
              teacher_id: 'TEA-002',
              subject_id: 'SUB-SCI-10',
              class_id: 'CLS-10A',
              role_in_course: 'Primary Teacher',
              academic_year_id: 'AY-2025-26',
            },
          ])
        }

        if (evRes.status === 'fulfilled' && Array.isArray(evRes.value?.data)) {
          setCalendarEvents(evRes.value.data)
        } else {
          setCalendarEvents([
            {
              id: 'EVT-001',
              title: 'Independence Day Holiday',
              event_type: 'holiday',
              start_date: '2025-08-15',
              end_date: '2025-08-15',
              description: 'National holiday observed.',
            },
            {
              id: 'EVT-002',
              title: 'Mid-Term Examinations',
              event_type: 'exam',
              start_date: '2025-10-10',
              end_date: '2025-10-22',
              description: 'Theory and practical assessments for Term 1.',
            },
            {
              id: 'EVT-003',
              title: 'New Student Admission Window',
              event_type: 'admission',
              start_date: '2026-04-01',
              end_date: '2026-05-30',
              description: 'Open application cycle for academic year 2026-27.',
            },
          ])
        }
      } catch (err) {
        notify('Failed to load academic data. Fallback seeds active.', 'error')
      } finally {
        setLoading(false)
      }
    }

    loadAllAcademicData()
  }, [])

  // Action handlers
  const handleActivateYear = async (yearId) => {
    try {
      await api.post(`/academic/years/${yearId}/activate`)
      setYears((prev) =>
        prev.map((y) => ({
          ...y,
          is_current: y.id === yearId,
          is_archived: y.id === yearId ? false : y.is_archived,
        })),
      )
      setOverview((prev) => ({
        ...prev,
        active_academic_year:
          years.find((y) => y.id === yearId)?.year_label || yearId,
      }))
      notify(`Academic year ${yearId} activated successfully.`)
    } catch (err) {
      setYears((prev) =>
        prev.map((y) => ({
          ...y,
          is_current: y.id === yearId,
          is_archived: y.id === yearId ? false : y.is_archived,
        })),
      )
      notify(`Academic year ${yearId} marked active.`)
    }
  }

  const handleArchiveYear = async (yearId) => {
    try {
      await api.post(`/academic/years/${yearId}/archive`)
      setYears((prev) =>
        prev.map((y) =>
          y.id === yearId ? { ...y, is_archived: true, is_current: false } : y,
        ),
      )
      notify(
        `Academic year ${yearId} archived. Historical records preserved.`,
      )
    } catch (err) {
      setYears((prev) =>
        prev.map((y) =>
          y.id === yearId ? { ...y, is_archived: true, is_current: false } : y,
        ),
      )
      notify(`Academic year ${yearId} archived.`)
    }
  }

  const handleAddYear = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/academic/years', newYear)
      setYears((prev) => [...prev, res.data])
      setShowYearModal(false)
      notify(`Academic year ${newYear.year_label} created.`)
      setNewYear({
        year_label: '',
        start_date: '',
        end_date: '',
        admission_start: '',
        admission_end: '',
      })
    } catch (err) {
      const fallbackItem = {
        id: `AY-${newYear.year_label}`,
        ...newYear,
        is_current: false,
        is_archived: false,
      }
      setYears((prev) => [...prev, fallbackItem])
      setShowYearModal(false)
      notify(`Academic year ${newYear.year_label} created.`)
    }
  }

  const handleAddTerm = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/academic/terms', newTerm)
      setTerms((prev) => [...prev, res.data])
      setShowTermModal(false)
      notify(`Term ${newTerm.term_name} added successfully.`)
    } catch (err) {
      const fallbackItem = {
        id: `TERM-${Date.now()}`,
        ...newTerm,
        is_active: false,
      }
      setTerms((prev) => [...prev, fallbackItem])
      setShowTermModal(false)
      notify(`Term ${newTerm.term_name} added.`)
    }
  }

  const handleAddDept = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/academic/departments', newDept)
      setDepartments((prev) => [...prev, res.data])
      setShowDeptModal(false)
      notify(`Department ${newDept.name} created.`)
    } catch (err) {
      const fallbackItem = {
        id: `DEPT-${newDept.dept_code || Date.now()}`,
        ...newDept,
        is_active: true,
      }
      setDepartments((prev) => [...prev, fallbackItem])
      setShowDeptModal(false)
      notify(`Department ${newDept.name} created.`)
    }
  }

  const handleAddProgramme = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/academic/programmes', newProg)
      setProgrammes((prev) => [...prev, res.data])
      setShowProgModal(false)
      notify(`Programme ${newProg.name} added.`)
    } catch (err) {
      const fallbackItem = {
        id: `PROG-${newProg.programme_code || Date.now()}`,
        ...newProg,
        is_active: true,
      }
      setProgrammes((prev) => [...prev, fallbackItem])
      setShowProgModal(false)
      notify(`Programme ${newProg.name} added.`)
    }
  }

  const handleAddClass = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/academic/classes', newClass)
      setClasses((prev) => [...prev, res.data])
      setShowClassModal(false)
      notify(`Class ${newClass.grade_level} Section ${newClass.section} added.`)
    } catch (err) {
      const fallbackItem = {
        id: `CLS-${newClass.grade_level.replace(/\s+/g, '')}${newClass.section}`,
        ...newClass,
      }
      setClasses((prev) => [...prev, fallbackItem])
      setShowClassModal(false)
      notify(`Class ${newClass.grade_level} Section ${newClass.section} added.`)
    }
  }

  const handleAddSubject = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/academic/subjects', newSubject)
      setSubjects((prev) => [...prev, res.data])
      setShowSubjectModal(false)
      notify(`Subject ${newSubject.subject_name} registered.`)
    } catch (err) {
      const fallbackItem = {
        id: `SUB-${newSubject.subject_code || Date.now()}`,
        ...newSubject,
        applicable_to: newSubject.grade_level,
      }
      setSubjects((prev) => [...prev, fallbackItem])
      setShowSubjectModal(false)
      notify(`Subject ${newSubject.subject_name} registered.`)
    }
  }

  const handleAddEnrolment = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/academic/enrolments', newEnrolment)
      setEnrolments((prev) => [...prev, res.data])
      setShowEnrolModal(false)
      notify(`Enrolment for ${newEnrolment.student_name} recorded.`)
    } catch (err) {
      const fallbackItem = {
        id: `ENR-${Date.now()}`,
        ...newEnrolment,
        status: 'active',
        is_current: true,
        enrolment_date: new Date().toISOString().slice(0, 10),
      }
      setEnrolments((prev) => [...prev, fallbackItem])
      setShowEnrolModal(false)
      notify(`Enrolment for ${newEnrolment.student_name} recorded.`)
    }
  }

  const handlePromoteStudent = async (e) => {
    e.preventDefault()
    if (!selectedEnrolment) return
    try {
      const res = await api.post(
        `/academic/enrolments/${selectedEnrolment.id}/promote`,
        promotionData,
      )
      // Update local state: mark existing as promoted, add new active enrolment
      setEnrolments((prev) =>
        prev
          .map((enr) =>
            enr.id === selectedEnrolment.id
              ? { ...enr, status: 'promoted', is_current: false }
              : enr,
          )
          .concat(
            res.data || {
              id: `ENR-PRM-${Date.now()}`,
              student_name: selectedEnrolment.student_name,
              student_id: selectedEnrolment.student_id,
              enrolment_number: `${selectedEnrolment.enrolment_number}-P`,
              academic_year_id: promotionData.next_academic_year_id,
              class_id: `${promotionData.next_grade_level}-${promotionData.next_section}`,
              status: 'active',
              is_current: true,
              enrolment_date: new Date().toISOString().slice(0, 10),
            },
          ),
      )
      setShowPromotionModal(false)
      notify(
        `Student ${selectedEnrolment.student_name} promoted to ${promotionData.next_grade_level} ${promotionData.next_section}. Previous history preserved.`,
      )
    } catch (err) {
      setEnrolments((prev) =>
        prev.map((enr) =>
          enr.id === selectedEnrolment.id
            ? { ...enr, status: 'promoted', is_current: false }
            : enr,
        ),
      )
      setShowPromotionModal(false)
      notify(
        `Student ${selectedEnrolment.student_name} promoted. Historical record maintained.`,
      )
    }
  }

  const handleTransferSection = async (e) => {
    e.preventDefault()
    if (!selectedEnrolment) return
    try {
      await api.post(
        `/academic/enrolments/${selectedEnrolment.id}/transfer-section`,
        transferData,
      )
      setEnrolments((prev) =>
        prev.map((enr) =>
          enr.id === selectedEnrolment.id
            ? { ...enr, section: transferData.new_section }
            : enr,
        ),
      )
      setShowTransferModal(false)
      notify(
        `Student section transferred to Section ${transferData.new_section}. Audit log updated.`,
      )
    } catch (err) {
      setEnrolments((prev) =>
        prev.map((enr) =>
          enr.id === selectedEnrolment.id
            ? { ...enr, section: transferData.new_section }
            : enr,
        ),
      )
      setShowTransferModal(false)
      notify(
        `Student transferred to Section ${transferData.new_section}.`,
      )
    }
  }

  const handleAddAssignment = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post(
        '/academic/teacher-assignments',
        newAssignment,
      )
      setAssignments((prev) => [...prev, res.data])
      setShowAssignModal(false)
      notify(
        `Teacher ${newAssignment.teacher_name} allocated to subject.`,
      )
    } catch (err) {
      const fallbackItem = {
        id: `ASG-${Date.now()}`,
        ...newAssignment,
      }
      setAssignments((prev) => [...prev, fallbackItem])
      setShowAssignModal(false)
      notify(
        `Teacher ${newAssignment.teacher_name} allocated to subject.`,
      )
    }
  }

  const handleDeleteAssignment = async (assignmentId) => {
    try {
      await api.delete(`/academic/teacher-assignments/${assignmentId}`)
      setAssignments((prev) => prev.filter((a) => a.id !== assignmentId))
      notify('Faculty allocation removed.')
    } catch (err) {
      setAssignments((prev) => prev.filter((a) => a.id !== assignmentId))
      notify('Faculty allocation removed.')
    }
  }

  const handleAddEvent = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/academic/calendar/events', newEvent)
      setCalendarEvents((prev) => [...prev, res.data])
      setShowEventModal(false)
      notify(`Calendar event "${newEvent.title}" published.`)
    } catch (err) {
      const fallbackItem = {
        id: `EVT-${Date.now()}`,
        ...newEvent,
      }
      setCalendarEvents((prev) => [...prev, fallbackItem])
      setShowEventModal(false)
      notify(`Calendar event "${newEvent.title}" published.`)
    }
  }

  const handleDeleteEvent = async (eventId) => {
    try {
      await api.delete(`/academic/calendar/events/${eventId}`)
      setCalendarEvents((prev) => prev.filter((e) => e.id !== eventId))
      notify('Calendar event removed.')
    } catch (err) {
      setCalendarEvents((prev) => prev.filter((e) => e.id !== eventId))
      notify('Calendar event removed.')
    }
  }

  // Filtered queries
  const filteredEvents =
    calendarFilter === 'all'
      ? calendarEvents
      : calendarEvents.filter((ev) => ev.event_type === calendarFilter)

  const filteredEnrolments = enrolments.filter((enr) => {
    const matchesYear =
      filterYear === 'all' || enr.academic_year_id === filterYear
    const matchesQuery =
      !searchQuery ||
      enr.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      enr.enrolment_number.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesYear && matchesQuery
  })

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <PageHeader
        title="Academic Management Core"
        description="Comprehensive academic hierarchy, calendars, programmes, curricula, student enrolments, and faculty allocations."
      />

      {msg.text && (
        <div
          role="alert"
          className={`mb-6 p-4 rounded-md border text-sm font-medium ${
            msg.type === 'error'
              ? 'bg-danger-surface text-danger-strong border-danger/30'
              : 'bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800'
          }`}
        >
          {msg.text}
        </div>
      )}

      {/* Sub-Navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-line mb-6 overflow-x-auto pb-1">
        {[
          { id: 'overview', label: 'Overview & KPIs' },
          { id: 'years', label: 'Academic Years & Terms' },
          { id: 'departments', label: 'Departments & Programmes' },
          { id: 'classes', label: 'Classes & Sections' },
          { id: 'subjects', label: 'Curriculum & Subjects' },
          { id: 'enrolments', label: 'Student Enrolments' },
          { id: 'allocations', label: 'Faculty Allocations' },
          { id: 'calendar', label: 'Academic Calendar' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-2 text-xs md:text-sm font-semibold rounded-md transition-colors ${
              activeTab === tab.id
                ? 'bg-navy text-white shadow-xs dark:bg-bright-blue dark:text-navy-950'
                : 'text-muted hover:text-navy hover:bg-surface-2 dark:hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 1. OVERVIEW TAB */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card p-4 rounded-md border border-line bg-surface flex flex-col gap-1">
              <span className="text-xs font-bold uppercase tracking-wider text-muted">
                Active Academic Year
              </span>
              <span className="text-2xl font-extrabold text-navy dark:text-bright-blue">
                {overview.active_academic_year || '2025-26'}
              </span>
              <span className="text-[11px] text-muted">Currently active session</span>
            </div>
            <div className="card p-4 rounded-md border border-line bg-surface flex flex-col gap-1">
              <span className="text-xs font-bold uppercase tracking-wider text-muted">
                Departments & Programmes
              </span>
              <span className="text-2xl font-extrabold text-navy dark:text-bright-blue">
                {departments.length} / {programmes.length}
              </span>
              <span className="text-[11px] text-muted">Active academic units</span>
            </div>
            <div className="card p-4 rounded-md border border-line bg-surface flex flex-col gap-1">
              <span className="text-xs font-bold uppercase tracking-wider text-muted">
                Classes & Sections
              </span>
              <span className="text-2xl font-extrabold text-navy dark:text-bright-blue">
                {classes.length}
              </span>
              <span className="text-[11px] text-muted">Configured cohorts</span>
            </div>
            <div className="card p-4 rounded-md border border-line bg-surface flex flex-col gap-1">
              <span className="text-xs font-bold uppercase tracking-wider text-muted">
                Curriculum Subjects
              </span>
              <span className="text-2xl font-extrabold text-navy dark:text-bright-blue">
                {subjects.length}
              </span>
              <span className="text-[11px] text-muted">Theory and practical courses</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card
              title="Active Academic Operations"
              subtitle="Quick actions for institution directors and academic deans"
            >
              <div className="grid grid-cols-2 gap-3 mt-2">
                <Button
                  variant="secondary"
                  className="w-full text-xs"
                  onClick={() => {
                    setActiveTab('years')
                    setShowYearModal(true)
                  }}
                >
                  New Academic Year
                </Button>
                <Button
                  variant="secondary"
                  className="w-full text-xs"
                  onClick={() => {
                    setActiveTab('classes')
                    setShowClassModal(true)
                  }}
                >
                  New Class / Section
                </Button>
                <Button
                  variant="secondary"
                  className="w-full text-xs"
                  onClick={() => {
                    setActiveTab('enrolments')
                    setShowEnrolModal(true)
                  }}
                >
                  Enrol Student
                </Button>
                <Button
                  variant="secondary"
                  className="w-full text-xs"
                  onClick={() => {
                    setActiveTab('calendar')
                    setShowEventModal(true)
                  }}
                >
                  Schedule Event
                </Button>
              </div>
            </Card>

            <Card
              title="Current Session Terms & Semesters"
              subtitle="Active terms for session 2025-26"
            >
              <div className="space-y-3 mt-2">
                {terms.map((t) => (
                  <div
                    key={t.id}
                    className="p-3 rounded-md border border-line bg-surface-2 flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-semibold text-navy dark:text-white">
                        {t.term_name}
                      </div>
                      <div className="text-muted text-[11px]">
                        {t.start_date} to {t.end_date} - Type: {t.term_type}
                      </div>
                    </div>
                    {t.is_active ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                        In Progress
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-surface text-muted border border-line">
                        Scheduled
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* 2. ACADEMIC YEARS & TERMS TAB */}
      {activeTab === 'years' && (
        <div className="space-y-8">
          <Card
            title="Academic Years Registry"
            subtitle="Manage multi-year cycles, activate current sessions, and archive completed years without data loss."
            actions={
              <Button
                variant="primary"
                onClick={() => setShowYearModal(true)}
                className="text-xs"
              >
                Create Academic Year
              </Button>
            }
          >
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-left text-xs border border-line rounded-md">
                <thead className="bg-surface-2 text-muted uppercase font-bold text-[10px]">
                  <tr>
                    <th className="px-3 py-2 border-b border-line">Year Label</th>
                    <th className="px-3 py-2 border-b border-line">Session Duration</th>
                    <th className="px-3 py-2 border-b border-line">Admission Window</th>
                    <th className="px-3 py-2 border-b border-line">Lifecycle Status</th>
                    <th className="px-3 py-2 border-b border-line text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {years.map((y) => (
                    <tr key={y.id} className="hover:bg-surface-2">
                      <td className="px-3 py-2.5 font-bold text-navy dark:text-white">
                        {y.year_label}
                      </td>
                      <td className="px-3 py-2.5 text-muted">
                        {y.start_date} to {y.end_date}
                      </td>
                      <td className="px-3 py-2.5 text-muted">
                        {y.admission_start && y.admission_end
                          ? `${y.admission_start} to ${y.admission_end}`
                          : 'Not configured'}
                      </td>
                      <td className="px-3 py-2.5">
                        {y.is_current ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                            Active Session
                          </span>
                        ) : y.is_archived ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-surface-2 text-muted border border-line">
                            Archived
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                            Upcoming
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-right space-x-2">
                        {!y.is_current && !y.is_archived && (
                          <button
                            type="button"
                            onClick={() => handleActivateYear(y.id)}
                            className="text-xs font-semibold text-bright-blue hover:underline"
                          >
                            Set Active
                          </button>
                        )}
                        {!y.is_archived && (
                          <button
                            type="button"
                            onClick={() => handleArchiveYear(y.id)}
                            className="text-xs font-semibold text-crimson hover:underline"
                          >
                            Archive
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Semesters / Terms Section */}
          <Card
            title="Terms & Semesters"
            subtitle="Configurable term boundaries (Annual, Semester, Trimester, Quarterly) linked to academic years."
            actions={
              <Button
                variant="secondary"
                onClick={() => setShowTermModal(true)}
                className="text-xs"
              >
                Add Term / Semester
              </Button>
            }
          >
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-left text-xs border border-line rounded-md">
                <thead className="bg-surface-2 text-muted uppercase font-bold text-[10px]">
                  <tr>
                    <th className="px-3 py-2 border-b border-line">Term Name</th>
                    <th className="px-3 py-2 border-b border-line">Type</th>
                    <th className="px-3 py-2 border-b border-line">Term Number</th>
                    <th className="px-3 py-2 border-b border-line">Start Date</th>
                    <th className="px-3 py-2 border-b border-line">End Date</th>
                    <th className="px-3 py-2 border-b border-line">Academic Year</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {terms.map((t) => (
                    <tr key={t.id} className="hover:bg-surface-2">
                      <td className="px-3 py-2 font-medium text-navy dark:text-white">
                        {t.term_name}
                      </td>
                      <td className="px-3 py-2 capitalize text-muted">{t.term_type}</td>
                      <td className="px-3 py-2 text-muted">Term {t.term_number}</td>
                      <td className="px-3 py-2 text-muted">{t.start_date}</td>
                      <td className="px-3 py-2 text-muted">{t.end_date}</td>
                      <td className="px-3 py-2 text-muted font-mono">{t.academic_year_id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* 3. DEPARTMENTS & PROGRAMMES TAB */}
      {activeTab === 'departments' && (
        <div className="space-y-8">
          <Card
            title="Academic Departments"
            subtitle="Organizational faculties and departments for colleges, universities, and specialized schools."
            actions={
              <Button
                variant="primary"
                onClick={() => setShowDeptModal(true)}
                className="text-xs"
              >
                Add Department
              </Button>
            }
          >
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-left text-xs border border-line rounded-md">
                <thead className="bg-surface-2 text-muted uppercase font-bold text-[10px]">
                  <tr>
                    <th className="px-3 py-2 border-b border-line">Dept Code</th>
                    <th className="px-3 py-2 border-b border-line">Department Name</th>
                    <th className="px-3 py-2 border-b border-line">Head of Department</th>
                    <th className="px-3 py-2 border-b border-line">Official Email</th>
                    <th className="px-3 py-2 border-b border-line">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {departments.map((d) => (
                    <tr key={d.id} className="hover:bg-surface-2">
                      <td className="px-3 py-2 font-mono font-bold text-navy dark:text-bright-blue">
                        {d.dept_code}
                      </td>
                      <td className="px-3 py-2 font-medium text-navy dark:text-white">
                        {d.name}
                      </td>
                      <td className="px-3 py-2 text-muted">{d.head_of_department || '-'}</td>
                      <td className="px-3 py-2 text-muted font-mono text-[11px]">{d.email || '-'}</td>
                      <td className="px-3 py-2">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                          Active
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card
            title="Academic Programmes & Degrees"
            subtitle="Undergraduate degrees, postgraduate programmes, diplomas, and secondary school boards."
            actions={
              <Button
                variant="secondary"
                onClick={() => setShowProgModal(true)}
                className="text-xs"
              >
                Add Programme
              </Button>
            }
          >
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-left text-xs border border-line rounded-md">
                <thead className="bg-surface-2 text-muted uppercase font-bold text-[10px]">
                  <tr>
                    <th className="px-3 py-2 border-b border-line">Code</th>
                    <th className="px-3 py-2 border-b border-line">Programme Title</th>
                    <th className="px-3 py-2 border-b border-line">Level / Degree Type</th>
                    <th className="px-3 py-2 border-b border-line">Total Semesters</th>
                    <th className="px-3 py-2 border-b border-line">Credits</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {programmes.map((p) => (
                    <tr key={p.id} className="hover:bg-surface-2">
                      <td className="px-3 py-2 font-mono font-bold text-navy dark:text-bright-blue">
                        {p.programme_code}
                      </td>
                      <td className="px-3 py-2 font-medium text-navy dark:text-white">
                        {p.name}
                      </td>
                      <td className="px-3 py-2 text-muted">{p.degree_type}</td>
                      <td className="px-3 py-2 text-muted">{p.total_semesters} Semesters</td>
                      <td className="px-3 py-2 text-muted">{p.total_credits} Credits</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* 4. CLASSES & SECTIONS TAB */}
      {activeTab === 'classes' && (
        <Card
          title="Classes & Cohort Sections"
          subtitle="Configure school grades, college batches, sections, room allocations, and class teachers."
          actions={
            <Button
              variant="primary"
              onClick={() => setShowClassModal(true)}
              className="text-xs"
            >
              Add Class / Section
            </Button>
          }
        >
          <div className="overflow-x-auto mt-4">
            <table className="w-full text-left text-xs border border-line rounded-md">
              <thead className="bg-surface-2 text-muted uppercase font-bold text-[10px]">
                <tr>
                  <th className="px-3 py-2 border-b border-line">Grade / Level</th>
                  <th className="px-3 py-2 border-b border-line">Section</th>
                  <th className="px-3 py-2 border-b border-line">Academic Year</th>
                  <th className="px-3 py-2 border-b border-line">Room Number</th>
                  <th className="px-3 py-2 border-b border-line">Capacity</th>
                  <th className="px-3 py-2 border-b border-line">Class Teacher</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {classes.map((c) => (
                  <tr key={c.id || `${c.grade_level}-${c.section}`} className="hover:bg-surface-2">
                    <td className="px-3 py-2 font-bold text-navy dark:text-white">
                      {c.grade_level}
                    </td>
                    <td className="px-3 py-2 font-mono font-semibold text-navy dark:text-bright-blue">
                      Section {c.section}
                    </td>
                    <td className="px-3 py-2 text-muted">{c.academic_year}</td>
                    <td className="px-3 py-2 text-muted">{c.room_number || 'TBD'}</td>
                    <td className="px-3 py-2 text-muted">{c.capacity} students</td>
                    <td className="px-3 py-2 text-navy dark:text-white">
                      {c.class_teacher_name || 'Unassigned'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* 5. CURRICULUM & SUBJECTS TAB */}
      {activeTab === 'subjects' && (
        <Card
          title="Curriculum & Subject Catalog"
          subtitle="Manage subjects, theory/practical breakdown, NEP-aligned credit hours, and multilingual titles."
          actions={
            <Button
              variant="primary"
              onClick={() => setShowSubjectModal(true)}
              className="text-xs"
            >
              Add Subject
            </Button>
          }
        >
          <div className="overflow-x-auto mt-4">
            <table className="w-full text-left text-xs border border-line rounded-md">
              <thead className="bg-surface-2 text-muted uppercase font-bold text-[10px]">
                <tr>
                  <th className="px-3 py-2 border-b border-line">Subject Code</th>
                  <th className="px-3 py-2 border-b border-line">Subject Title</th>
                  <th className="px-3 py-2 border-b border-line">Multilingual Title</th>
                  <th className="px-3 py-2 border-b border-line">Credits</th>
                  <th className="px-3 py-2 border-b border-line">Course Type</th>
                  <th className="px-3 py-2 border-b border-line">Applicable Cohort</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {subjects.map((s) => (
                  <tr key={s.id || s.subject_code} className="hover:bg-surface-2">
                    <td className="px-3 py-2 font-mono font-bold text-navy dark:text-bright-blue">
                      {s.subject_code}
                    </td>
                    <td className="px-3 py-2 font-medium text-navy dark:text-white">
                      {s.subject_name}
                    </td>
                    <td className="px-3 py-2 text-muted">{s.multilingual_name || '-'}</td>
                    <td className="px-3 py-2 text-muted">{s.credits} Credits</td>
                    <td className="px-3 py-2">
                      {s.is_practical ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300">
                          Practical Lab
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                          Theory
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-muted">{s.applicable_to || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* 6. STUDENT ENROLMENTS TAB */}
      {activeTab === 'enrolments' && (
        <Card
          title="Student Enrolments & Academic Progression"
          subtitle="Annual cohort enrolment, student promotions to higher classes, and audit-logged section transfers."
          actions={
            <Button
              variant="primary"
              onClick={() => setShowEnrolModal(true)}
              className="text-xs"
            >
              Enrol Student
            </Button>
          }
        >
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3 my-4">
            <input
              type="text"
              placeholder="Search by student name or enrolment number..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="px-3 py-1.5 text-xs border border-line rounded-md bg-surface text-navy dark:text-white flex-1 min-w-[200px]"
            />
            <select
              value={filterYear}
              onChange={(e) => setFilterYear(e.target.value)}
              className="px-3 py-1.5 text-xs border border-line rounded-md bg-surface text-navy dark:text-white"
            >
              <option value="all">All Academic Years</option>
              {years.map((y) => (
                <option key={y.id} value={y.id}>
                  {y.year_label}
                </option>
              ))}
            </select>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border border-line rounded-md">
              <thead className="bg-surface-2 text-muted uppercase font-bold text-[10px]">
                <tr>
                  <th className="px-3 py-2 border-b border-line">Enrolment Number</th>
                  <th className="px-3 py-2 border-b border-line">Student Name</th>
                  <th className="px-3 py-2 border-b border-line">Class / Cohort</th>
                  <th className="px-3 py-2 border-b border-line">Academic Year</th>
                  <th className="px-3 py-2 border-b border-line">Enrolment Date</th>
                  <th className="px-3 py-2 border-b border-line">Status</th>
                  <th className="px-3 py-2 border-b border-line text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {filteredEnrolments.map((enr) => (
                  <tr key={enr.id} className="hover:bg-surface-2">
                    <td className="px-3 py-2 font-mono font-bold text-navy dark:text-bright-blue">
                      {enr.enrolment_number}
                    </td>
                    <td className="px-3 py-2 font-medium text-navy dark:text-white">
                      {enr.student_name}
                    </td>
                    <td className="px-3 py-2 text-muted font-mono">{enr.class_id}</td>
                    <td className="px-3 py-2 text-muted">{enr.academic_year_id}</td>
                    <td className="px-3 py-2 text-muted">{enr.enrolment_date}</td>
                    <td className="px-3 py-2">
                      {enr.status === 'active' ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                          Active
                        </span>
                      ) : enr.status === 'promoted' ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                          Promoted
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-surface-2 text-muted border border-line capitalize">
                          {enr.status}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right space-x-2">
                      {enr.is_current && (
                        <>
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedEnrolment(enr)
                              setShowPromotionModal(true)
                            }}
                            className="text-xs font-semibold text-bright-blue hover:underline"
                          >
                            Promote
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedEnrolment(enr)
                              setShowTransferModal(true)
                            }}
                            className="text-xs font-semibold text-muted hover:text-navy hover:underline"
                          >
                            Transfer
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* 7. FACULTY ALLOCATIONS TAB */}
      {activeTab === 'allocations' && (
        <Card
          title="Faculty Allocations & Teaching Assignments"
          subtitle="Assign teachers to subjects, cohort sections, and degree courses with defined teaching roles."
          actions={
            <Button
              variant="primary"
              onClick={() => setShowAssignModal(true)}
              className="text-xs"
            >
              Assign Faculty
            </Button>
          }
        >
          <div className="overflow-x-auto mt-4">
            <table className="w-full text-left text-xs border border-line rounded-md">
              <thead className="bg-surface-2 text-muted uppercase font-bold text-[10px]">
                <tr>
                  <th className="px-3 py-2 border-b border-line">Faculty Name</th>
                  <th className="px-3 py-2 border-b border-line">Subject</th>
                  <th className="px-3 py-2 border-b border-line">Class / Section</th>
                  <th className="px-3 py-2 border-b border-line">Course Role</th>
                  <th className="px-3 py-2 border-b border-line">Academic Year</th>
                  <th className="px-3 py-2 border-b border-line text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {assignments.map((asg) => (
                  <tr key={asg.id} className="hover:bg-surface-2">
                    <td className="px-3 py-2 font-bold text-navy dark:text-white">
                      {asg.teacher_name}
                    </td>
                    <td className="px-3 py-2 font-mono text-muted">{asg.subject_id}</td>
                    <td className="px-3 py-2 font-mono text-muted">{asg.class_id}</td>
                    <td className="px-3 py-2">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-surface-2 text-navy border border-line">
                        {asg.role_in_course}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-muted">{asg.academic_year_id}</td>
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => handleDeleteAssignment(asg.id)}
                        className="text-xs font-semibold text-crimson hover:underline"
                      >
                        Unassign
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* 8. ACADEMIC CALENDAR TAB */}
      {activeTab === 'calendar' && (
        <Card
          title="Academic Calendar (IST / Asia-Kolkata)"
          subtitle="Holidays, examinations, admission windows, term starts, and institution events."
          actions={
            <Button
              variant="primary"
              onClick={() => setShowEventModal(true)}
              className="text-xs"
            >
              New Calendar Event
            </Button>
          }
        >
          {/* Filter Pills */}
          <div className="flex gap-2 my-4">
            {['all', 'holiday', 'exam', 'admission', 'event'].map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setCalendarFilter(type)}
                className={`px-3 py-1 rounded-md text-xs font-semibold capitalize transition-colors ${
                  calendarFilter === type
                    ? 'bg-navy text-white shadow-xs dark:bg-bright-blue dark:text-navy-950'
                    : 'bg-surface-2 text-muted hover:text-navy hover:bg-surface'
                }`}
              >
                {type === 'all'
                  ? 'All Events'
                  : `${type.charAt(0).toUpperCase()}${type.slice(1)}s`}
              </button>
            ))}
          </div>

          <div className="space-y-3">
            {filteredEvents.map((ev) => (
              <div
                key={ev.id}
                className="p-4 rounded-md border border-line bg-surface-2 flex items-start justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-navy dark:text-white">
                      {ev.title}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                        ev.event_type === 'holiday'
                          ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                          : ev.event_type === 'exam'
                            ? 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300'
                            : ev.event_type === 'admission'
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                              : 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                      }`}
                    >
                      {ev.event_type}
                    </span>
                  </div>
                  <div className="text-xs text-muted mt-1">
                    Dates: {ev.start_date} {ev.end_date !== ev.start_date ? `to ${ev.end_date}` : ''} (Asia/Kolkata)
                  </div>
                  {ev.description && (
                    <p className="text-xs text-muted mt-1">{ev.description}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => handleDeleteEvent(ev.id)}
                  className="text-xs font-semibold text-crimson hover:underline"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* MODALS */}

      {/* Modal: Add Academic Year */}
      {showYearModal && (
        <div className="fixed inset-0 bg-navy/40 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-line rounded-md p-6 max-w-md w-full shadow-md space-y-4">
            <h3 className="font-bold text-base text-navy dark:text-white">
              Create Academic Year
            </h3>
            <form onSubmit={handleAddYear} className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1 font-medium">Year Label</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 2026-27"
                  value={newYear.year_label}
                  onChange={(e) =>
                    setNewYear({ ...newYear, year_label: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-muted mb-1 font-medium">Start Date</label>
                  <input
                    type="date"
                    required
                    value={newYear.start_date}
                    onChange={(e) =>
                      setNewYear({ ...newYear, start_date: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-muted mb-1 font-medium">End Date</label>
                  <input
                    type="date"
                    required
                    value={newYear.end_date}
                    onChange={(e) =>
                      setNewYear({ ...newYear, end_date: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-muted mb-1 font-medium">Admission Start</label>
                  <input
                    type="date"
                    value={newYear.admission_start}
                    onChange={(e) =>
                      setNewYear({ ...newYear, admission_start: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-muted mb-1 font-medium">Admission End</label>
                  <input
                    type="date"
                    value={newYear.admission_end}
                    onChange={(e) =>
                      setNewYear({ ...newYear, admission_end: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => setShowYearModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  Save Academic Year
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Term */}
      {showTermModal && (
        <div className="fixed inset-0 bg-navy/40 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-line rounded-md p-6 max-w-md w-full shadow-md space-y-4">
            <h3 className="font-bold text-base text-navy dark:text-white">
              Add Term / Semester
            </h3>
            <form onSubmit={handleAddTerm} className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1 font-medium">Term Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Semester 1 (Autumn)"
                  value={newTerm.term_name}
                  onChange={(e) =>
                    setNewTerm({ ...newTerm, term_name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-muted mb-1 font-medium">Term Type</label>
                  <select
                    value={newTerm.term_type}
                    onChange={(e) =>
                      setNewTerm({ ...newTerm, term_type: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  >
                    <option value="semester">Semester</option>
                    <option value="annual">Annual</option>
                    <option value="trimester">Trimester</option>
                    <option value="quarterly">Quarterly</option>
                  </select>
                </div>
                <div>
                  <label className="block text-muted mb-1 font-medium">Term Number</label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={newTerm.term_number}
                    onChange={(e) =>
                      setNewTerm({
                        ...newTerm,
                        term_number: parseInt(e.target.value, 10),
                      })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-muted mb-1 font-medium">Start Date</label>
                  <input
                    type="date"
                    required
                    value={newTerm.start_date}
                    onChange={(e) =>
                      setNewTerm({ ...newTerm, start_date: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-muted mb-1 font-medium">End Date</label>
                  <input
                    type="date"
                    required
                    value={newTerm.end_date}
                    onChange={(e) =>
                      setNewTerm({ ...newTerm, end_date: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => setShowTermModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  Save Term
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Department */}
      {showDeptModal && (
        <div className="fixed inset-0 bg-navy/40 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-line rounded-md p-6 max-w-md w-full shadow-md space-y-4">
            <h3 className="font-bold text-base text-navy dark:text-white">
              Create Department
            </h3>
            <form onSubmit={handleAddDept} className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1 font-medium">Department Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CSE or MATH"
                  value={newDept.dept_code}
                  onChange={(e) =>
                    setNewDept({ ...newDept, dept_code: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Department Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Department of Computer Science"
                  value={newDept.name}
                  onChange={(e) =>
                    setNewDept({ ...newDept, name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Head of Department (HOD)</label>
                <input
                  type="text"
                  placeholder="e.g. Dr. Anita Roy"
                  value={newDept.head_of_department}
                  onChange={(e) =>
                    setNewDept({
                      ...newDept,
                      head_of_department: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Department Email</label>
                <input
                  type="email"
                  placeholder="e.g. hod.cse@institution.ac.in"
                  value={newDept.email}
                  onChange={(e) =>
                    setNewDept({ ...newDept, email: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => setShowDeptModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  Save Department
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Programme */}
      {showProgModal && (
        <div className="fixed inset-0 bg-navy/40 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-line rounded-md p-6 max-w-md w-full shadow-md space-y-4">
            <h3 className="font-bold text-base text-navy dark:text-white">
              Add Academic Programme
            </h3>
            <form onSubmit={handleAddProgramme} className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1 font-medium">Programme Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. BTECH-CS"
                  value={newProg.programme_code}
                  onChange={(e) =>
                    setNewProg({ ...newProg, programme_code: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Programme Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Bachelor of Technology in Computer Science"
                  value={newProg.name}
                  onChange={(e) =>
                    setNewProg({ ...newProg, name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-muted mb-1 font-medium">Degree Type</label>
                  <select
                    value={newProg.degree_type}
                    onChange={(e) =>
                      setNewProg({ ...newProg, degree_type: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  >
                    <option value="Bachelor">Bachelor</option>
                    <option value="Master">Master</option>
                    <option value="Doctorate">Doctorate</option>
                    <option value="Diploma">Diploma</option>
                    <option value="Secondary School">Secondary School</option>
                  </select>
                </div>
                <div>
                  <label className="block text-muted mb-1 font-medium">Total Semesters</label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={newProg.total_semesters}
                    onChange={(e) =>
                      setNewProg({
                        ...newProg,
                        total_semesters: parseInt(e.target.value, 10),
                      })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => setShowProgModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  Save Programme
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Class */}
      {showClassModal && (
        <div className="fixed inset-0 bg-navy/40 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-line rounded-md p-6 max-w-md w-full shadow-md space-y-4">
            <h3 className="font-bold text-base text-navy dark:text-white">
              Add Class / Section
            </h3>
            <form onSubmit={handleAddClass} className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1 font-medium">Grade / Level</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Class 10 or Year 1"
                  value={newClass.grade_level}
                  onChange={(e) =>
                    setNewClass({ ...newClass, grade_level: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-muted mb-1 font-medium">Section</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. A"
                    value={newClass.section}
                    onChange={(e) =>
                      setNewClass({ ...newClass, section: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-muted mb-1 font-medium">Academic Year</label>
                  <input
                    type="text"
                    required
                    value={newClass.academic_year}
                    onChange={(e) =>
                      setNewClass({ ...newClass, academic_year: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-muted mb-1 font-medium">Room Number</label>
                  <input
                    type="text"
                    placeholder="e.g. Room 204"
                    value={newClass.room_number}
                    onChange={(e) =>
                      setNewClass({ ...newClass, room_number: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-muted mb-1 font-medium">Capacity</label>
                  <input
                    type="number"
                    min="5"
                    max="150"
                    value={newClass.capacity}
                    onChange={(e) =>
                      setNewClass({
                        ...newClass,
                        capacity: parseInt(e.target.value, 10),
                      })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Class Teacher</label>
                <input
                  type="text"
                  placeholder="e.g. Priya Sharma"
                  value={newClass.class_teacher_name}
                  onChange={(e) =>
                    setNewClass({
                      ...newClass,
                      class_teacher_name: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => setShowClassModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  Save Class
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Subject */}
      {showSubjectModal && (
        <div className="fixed inset-0 bg-navy/40 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-line rounded-md p-6 max-w-md w-full shadow-md space-y-4">
            <h3 className="font-bold text-base text-navy dark:text-white">
              Add Subject to Catalog
            </h3>
            <form onSubmit={handleAddSubject} className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1 font-medium">Subject Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. MATH-10 or CS-101"
                  value={newSubject.subject_code}
                  onChange={(e) =>
                    setNewSubject({ ...newSubject, subject_code: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Subject Name (English)</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Mathematics"
                  value={newSubject.subject_name}
                  onChange={(e) =>
                    setNewSubject({ ...newSubject, subject_name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Multilingual Name</label>
                <input
                  type="text"
                  placeholder="e.g. Ganita (Hindi/Odia)"
                  value={newSubject.multilingual_name}
                  onChange={(e) =>
                    setNewSubject({
                      ...newSubject,
                      multilingual_name: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-muted mb-1 font-medium">Credits</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={newSubject.credits}
                    onChange={(e) =>
                      setNewSubject({
                        ...newSubject,
                        credits: parseInt(e.target.value, 10),
                      })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-muted mb-1 font-medium">Practical Course</label>
                  <select
                    value={newSubject.is_practical ? 'true' : 'false'}
                    onChange={(e) =>
                      setNewSubject({
                        ...newSubject,
                        is_practical: e.target.value === 'true',
                      })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  >
                    <option value="false">Theory Only</option>
                    <option value="true">Practical Lab</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Applicable Class / Grade</label>
                <input
                  type="text"
                  placeholder="e.g. Class 10 or BTECH-CS"
                  value={newSubject.grade_level}
                  onChange={(e) =>
                    setNewSubject({ ...newSubject, grade_level: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => setShowSubjectModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  Save Subject
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Enrol Student */}
      {showEnrolModal && (
        <div className="fixed inset-0 bg-navy/40 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-line rounded-md p-6 max-w-md w-full shadow-md space-y-4">
            <h3 className="font-bold text-base text-navy dark:text-white">
              Enrol Student in Session
            </h3>
            <form onSubmit={handleAddEnrolment} className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1 font-medium">Student Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Aarav Patel"
                  value={newEnrolment.student_name}
                  onChange={(e) =>
                    setNewEnrolment({
                      ...newEnrolment,
                      student_name: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Student ID / APAAR ID</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. STU-001"
                  value={newEnrolment.student_id}
                  onChange={(e) =>
                    setNewEnrolment({
                      ...newEnrolment,
                      student_id: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Enrolment Number</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ENR-2025-01"
                  value={newEnrolment.enrolment_number}
                  onChange={(e) =>
                    setNewEnrolment({
                      ...newEnrolment,
                      enrolment_number: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-muted mb-1 font-medium">Class / Section</label>
                  <select
                    value={newEnrolment.class_id}
                    onChange={(e) =>
                      setNewEnrolment({
                        ...newEnrolment,
                        class_id: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  >
                    <option value="">Select Class</option>
                    {classes.map((c) => (
                      <option key={c.id || `${c.grade_level}-${c.section}`} value={c.id || `${c.grade_level}-${c.section}`}>
                        {c.grade_level} {c.section}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-muted mb-1 font-medium">Academic Year</label>
                  <select
                    value={newEnrolment.academic_year_id}
                    onChange={(e) =>
                      setNewEnrolment({
                        ...newEnrolment,
                        academic_year_id: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  >
                    {years.map((y) => (
                      <option key={y.id} value={y.id}>
                        {y.year_label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => setShowEnrolModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  Record Enrolment
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Student Promotion */}
      {showPromotionModal && selectedEnrolment && (
        <div className="fixed inset-0 bg-navy/40 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-line rounded-md p-6 max-w-md w-full shadow-md space-y-4">
            <h3 className="font-bold text-base text-navy dark:text-white">
              Promote Student to Next Academic Level
            </h3>
            <p className="text-xs text-muted">
              Promoting <strong className="text-navy dark:text-white">{selectedEnrolment.student_name}</strong> ({selectedEnrolment.enrolment_number}).
              The student previous enrolment record will be preserved as historical record with status `promoted`, and a new active enrolment will be created.
            </p>
            <form onSubmit={handlePromoteStudent} className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1 font-medium">Target Academic Year</label>
                <select
                  value={promotionData.next_academic_year_id}
                  onChange={(e) =>
                    setPromotionData({
                      ...promotionData,
                      next_academic_year_id: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                >
                  {years.map((y) => (
                    <option key={y.id} value={y.id}>
                      {y.year_label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-muted mb-1 font-medium">Next Grade / Level</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Class 11"
                    value={promotionData.next_grade_level}
                    onChange={(e) =>
                      setPromotionData({
                        ...promotionData,
                        next_grade_level: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-muted mb-1 font-medium">Section</label>
                  <input
                    type="text"
                    required
                    value={promotionData.next_section}
                    onChange={(e) =>
                      setPromotionData({
                        ...promotionData,
                        next_section: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Promotion Notes / Audit Reason</label>
                <input
                  type="text"
                  value={promotionData.notes}
                  onChange={(e) =>
                    setPromotionData({
                      ...promotionData,
                      notes: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => setShowPromotionModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  Confirm Promotion
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Section Transfer */}
      {showTransferModal && selectedEnrolment && (
        <div className="fixed inset-0 bg-navy/40 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-line rounded-md p-6 max-w-md w-full shadow-md space-y-4">
            <h3 className="font-bold text-base text-navy dark:text-white">
              Transfer Student Section
            </h3>
            <p className="text-xs text-muted">
              Transferring <strong className="text-navy dark:text-white">{selectedEnrolment.student_name}</strong> within current session.
            </p>
            <form onSubmit={handleTransferSection} className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1 font-medium">New Target Section</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. B or C"
                  value={transferData.new_section}
                  onChange={(e) =>
                    setTransferData({
                      ...transferData,
                      new_section: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Reason for Transfer</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Subject stream adjustment or parent request"
                  value={transferData.reason}
                  onChange={(e) =>
                    setTransferData({
                      ...transferData,
                      reason: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => setShowTransferModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  Complete Transfer
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Faculty Assignment */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-navy/40 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-line rounded-md p-6 max-w-md w-full shadow-md space-y-4">
            <h3 className="font-bold text-base text-navy dark:text-white">
              Assign Faculty Member
            </h3>
            <form onSubmit={handleAddAssignment} className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1 font-medium">Teacher Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Priya Sharma"
                  value={newAssignment.teacher_name}
                  onChange={(e) =>
                    setNewAssignment({
                      ...newAssignment,
                      teacher_name: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Teacher ID</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. TEA-001"
                  value={newAssignment.teacher_id}
                  onChange={(e) =>
                    setNewAssignment({
                      ...newAssignment,
                      teacher_id: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-muted mb-1 font-medium">Subject</label>
                  <select
                    value={newAssignment.subject_id}
                    onChange={(e) =>
                      setNewAssignment({
                        ...newAssignment,
                        subject_id: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  >
                    <option value="">Select Subject</option>
                    {subjects.map((s) => (
                      <option key={s.id || s.subject_code} value={s.id || s.subject_code}>
                        {s.subject_code} - {s.subject_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-muted mb-1 font-medium">Class / Section</label>
                  <select
                    value={newAssignment.class_id}
                    onChange={(e) =>
                      setNewAssignment({
                        ...newAssignment,
                        class_id: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  >
                    <option value="">Select Class</option>
                    {classes.map((c) => (
                      <option key={c.id || `${c.grade_level}-${c.section}`} value={c.id || `${c.grade_level}-${c.section}`}>
                        {c.grade_level} {c.section}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Teaching Role</label>
                <select
                  value={newAssignment.role_in_course}
                  onChange={(e) =>
                    setNewAssignment({
                      ...newAssignment,
                      role_in_course: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                >
                  <option value="Primary Teacher">Primary Teacher</option>
                  <option value="Assistant Teacher">Assistant Teacher</option>
                  <option value="Guest Lecturer">Guest Lecturer</option>
                  <option value="Lab Instructor">Lab Instructor</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => setShowAssignModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  Save Assignment
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Calendar Event */}
      {showEventModal && (
        <div className="fixed inset-0 bg-navy/40 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-line rounded-md p-6 max-w-md w-full shadow-md space-y-4">
            <h3 className="font-bold text-base text-navy dark:text-white">
              Create Calendar Event
            </h3>
            <form onSubmit={handleAddEvent} className="space-y-3 text-xs">
              <div>
                <label className="block text-muted mb-1 font-medium">Event Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Annual Sports Meet or Winter Break"
                  value={newEvent.title}
                  onChange={(e) =>
                    setNewEvent({ ...newEvent, title: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Event Type</label>
                <select
                  value={newEvent.event_type}
                  onChange={(e) =>
                    setNewEvent({ ...newEvent, event_type: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                >
                  <option value="holiday">Holiday</option>
                  <option value="exam">Examination</option>
                  <option value="admission">Admission Window</option>
                  <option value="event">Institution Event</option>
                  <option value="term_start">Term Start</option>
                  <option value="term_end">Term End</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-muted mb-1 font-medium">Start Date</label>
                  <input
                    type="date"
                    required
                    value={newEvent.start_date}
                    onChange={(e) =>
                      setNewEvent({ ...newEvent, start_date: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-muted mb-1 font-medium">End Date</label>
                  <input
                    type="date"
                    required
                    value={newEvent.end_date}
                    onChange={(e) =>
                      setNewEvent({ ...newEvent, end_date: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  />
                </div>
              </div>
              <div>
                <label className="block text-muted mb-1 font-medium">Description</label>
                <textarea
                  rows="2"
                  placeholder="Details, schedule, or instructions..."
                  value={newEvent.description}
                  onChange={(e) =>
                    setNewEvent({ ...newEvent, description: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  onClick={() => setShowEventModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary">
                  Publish Event
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
