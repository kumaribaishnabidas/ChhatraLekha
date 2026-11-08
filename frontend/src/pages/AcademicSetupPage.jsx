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
    active_academic_year: '',
    current_academic_year: '',
    total_departments: 0,
    total_programmes: 0,
    total_classes: 0,
    total_subjects: 0,
    total_enrolled_students: 0,
    total_students_enrolled: 0,
    total_faculty_assigned: 0,
    total_faculty_assignments: 0,
    recent_events: [],
  })
  const [modalError, setModalError] = useState('')
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
    admission_start_date: '',
    admission_end_date: '',
  })
  const [newTerm, setNewTerm] = useState({
    name: '',
    term_name: '',
    term_type: 'semester',
    term_number: 1,
    start_date: '',
    end_date: '',
    academic_year: '2025-26',
    academic_year_id: 'AY-2025-26',
  })
  const [newDept, setNewDept] = useState({
    department_code: '',
    dept_code: '',
    name: '',
    head_of_department_name: '',
    head_of_department: '',
    contact_email: '',
    email: '',
    description: '',
  })
  const [newProg, setNewProg] = useState({
    programme_code: '',
    name: '',
    degree_type: 'Bachelor',
    degree_awarded: 'Bachelor',
    academic_level: 'UNDERGRADUATE',
    department_id: '',
    total_semesters: 8,
    duration_years: 4,
    total_credits: 160,
    approved_intake: 60,
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
    subject_name_hi: '',
    credits: 4,
    is_practical: false,
    department_id: '',
    grade_level: 'Class 10',
    applicable_to: 'Class 10',
  })
  const [newEnrolment, setNewEnrolment] = useState({
    student_name: '',
    student_id: '',
    enrolment_number: '',
    roll_number: '',
    academic_year_id: 'AY-2025-26',
    academic_year: '2025-26',
    class_id: '',
  })
  const [promotionData, setPromotionData] = useState({
    next_academic_year_id: 'AY-2026-27',
    target_academic_year: '2026-27',
    next_grade_level: 'Class 11',
    target_grade_or_semester: 'Class 11',
    next_section: 'A',
    target_section: 'A',
    notes: 'Annual progression',
    remarks: 'Annual progression',
  })
  const [transferData, setTransferData] = useState({
    target_class_id: '',
    new_section: 'B',
    target_section: 'B',
    reason: 'Administrative transfer',
    transfer_reason: 'Administrative transfer',
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

  const errorMessage = (err) => {
    const detail = err?.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
    }
    return err?.message || 'Operation failed. Please check inputs and retry.'
  }

  const openModal = (setter, target = null) => {
    setModalError('')
    if (target) {
      setSelectedEnrolment(target)
    }
    setter(true)
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
        setYears(yrRes.status === 'fulfilled' && Array.isArray(yrRes.value?.data) ? yrRes.value.data : [])
        setTerms(tmRes.status === 'fulfilled' && Array.isArray(tmRes.value?.data) ? tmRes.value.data : [])
        setDepartments(dpRes.status === 'fulfilled' && Array.isArray(dpRes.value?.data) ? dpRes.value.data : [])
        setProgrammes(prRes.status === 'fulfilled' && Array.isArray(prRes.value?.data) ? prRes.value.data : [])
        setClasses(clRes.status === 'fulfilled' && Array.isArray(clRes.value?.data) ? clRes.value.data : [])
        setSubjects(sbRes.status === 'fulfilled' && Array.isArray(sbRes.value?.data) ? sbRes.value.data : [])
        setEnrolments(enRes.status === 'fulfilled' && Array.isArray(enRes.value?.data) ? enRes.value.data : [])
        setAssignments(taRes.status === 'fulfilled' && Array.isArray(taRes.value?.data) ? taRes.value.data : [])
        setCalendarEvents(evRes.status === 'fulfilled' && Array.isArray(evRes.value?.data) ? evRes.value.data : [])

        const failed = [ovRes, yrRes, tmRes, dpRes, prRes, clRes, sbRes, enRes, taRes, evRes].filter(
          (r) => r.status === 'rejected',
        )
        if (failed.length > 0) {
          notify('Some academic records could not be loaded from the server.', 'error')
        }
      } catch (err) {
        notify('Failed to load academic data.', 'error')
      } finally {
        setLoading(false)
      }
    }

    loadAllAcademicData()
  }, [])

  // Action handlers
  const handleActivateYear = async (yearId) => {
    try {
      const res = await api.post(`/academic/years/${yearId}/activate`)
      setYears((prev) =>
        prev.map((y) => ({
          ...y,
          is_current: (y.id || y._id) === yearId,
          status: (y.id || y._id) === yearId ? 'ACTIVE' : y.status,
          is_archived: (y.id || y._id) === yearId ? false : y.is_archived,
        })),
      )
      if (res.data?.year_label) {
        setOverview((prev) => ({
          ...prev,
          current_academic_year: res.data.year_label,
          active_academic_year: res.data.year_label,
        }))
      }
      notify(`Academic year ${yearId} activated successfully.`)
    } catch (err) {
      notify(errorMessage(err), 'error')
    }
  }

  const handleArchiveYear = async (yearId) => {
    try {
      await api.post(`/academic/years/${yearId}/archive`)
      setYears((prev) =>
        prev.map((y) =>
          (y.id || y._id) === yearId ? { ...y, status: 'ARCHIVED', is_archived: true, is_current: false } : y,
        ),
      )
      notify(
        `Academic year ${yearId} archived. Historical records preserved.`,
      )
    } catch (err) {
      notify(errorMessage(err), 'error')
    }
  }

  const handleAddYear = async (e) => {
    e.preventDefault()
    setModalError('')
    try {
      const payload = {
        year_label: newYear.year_label,
        start_date: newYear.start_date,
        end_date: newYear.end_date,
        admission_start_date: newYear.admission_start_date || newYear.admission_start || null,
        admission_end_date: newYear.admission_end_date || newYear.admission_end || null,
        is_current: false,
        status: 'UPCOMING',
      }
      const res = await api.post('/academic/years', payload)
      setYears((prev) => [...prev, res.data])
      setShowYearModal(false)
      notify(`Academic year ${newYear.year_label} created.`)
      setNewYear({
        year_label: '',
        start_date: '',
        end_date: '',
        admission_start: '',
        admission_end: '',
        admission_start_date: '',
        admission_end_date: '',
      })
    } catch (err) {
      const msgText = errorMessage(err)
      setModalError(msgText)
      notify(msgText, 'error')
    }
  }

  const handleAddTerm = async (e) => {
    e.preventDefault()
    setModalError('')
    try {
      const payload = {
        name: newTerm.name || newTerm.term_name,
        term_type: (newTerm.term_type || 'SEMESTER').toUpperCase(),
        academic_year: (newTerm.academic_year || newTerm.academic_year_id || overview?.current_academic_year || '2025-26').replace(/^AY-/, ''),
        start_date: newTerm.start_date,
        end_date: newTerm.end_date,
        status: 'ACTIVE',
      }
      const res = await api.post('/academic/terms', payload)
      setTerms((prev) => [...prev, res.data])
      setShowTermModal(false)
      notify(`Term ${payload.name} added successfully.`)
      setNewTerm({
        name: '',
        term_name: '',
        term_type: 'semester',
        term_number: 1,
        start_date: '',
        end_date: '',
        academic_year: '2025-26',
        academic_year_id: 'AY-2025-26',
      })
    } catch (err) {
      const msgText = errorMessage(err)
      setModalError(msgText)
      notify(msgText, 'error')
    }
  }

  const handleAddDept = async (e) => {
    e.preventDefault()
    setModalError('')
    try {
      const payload = {
        department_code: (newDept.department_code || newDept.dept_code || '').toUpperCase(),
        name: newDept.name,
        head_of_department_name: newDept.head_of_department_name || newDept.head_of_department || null,
        contact_email: newDept.contact_email || newDept.email || null,
        description: newDept.description || null,
      }
      const res = await api.post('/academic/departments', payload)
      setDepartments((prev) => [...prev, res.data])
      setShowDeptModal(false)
      notify(`Department ${newDept.name} created.`)
      setNewDept({
        department_code: '',
        dept_code: '',
        name: '',
        head_of_department_name: '',
        head_of_department: '',
        contact_email: '',
        email: '',
        description: '',
      })
    } catch (err) {
      const msgText = errorMessage(err)
      setModalError(msgText)
      notify(msgText, 'error')
    }
  }

  const handleAddProgramme = async (e) => {
    e.preventDefault()
    setModalError('')
    try {
      const levelMap = {
        'Bachelor': 'UNDERGRADUATE',
        'Master': 'POSTGRADUATE',
        'Doctorate': 'DOCTORAL',
        'Diploma': 'DIPLOMA',
        'Secondary School': 'SECONDARY',
      }
      const totalSem = Number(newProg.total_semesters) || 8
      const payload = {
        programme_code: (newProg.programme_code || '').toUpperCase(),
        name: newProg.name,
        department_id: newProg.department_id || null,
        academic_level: newProg.academic_level || levelMap[newProg.degree_type] || 'UNDERGRADUATE',
        duration_years: Number(newProg.duration_years) || Math.max(1, Math.ceil(totalSem / 2)),
        total_semesters: totalSem,
        degree_awarded: newProg.degree_awarded || newProg.degree_type || 'Degree',
        curriculum_framework: newProg.curriculum_framework || 'NEP 2020 Aligned',
        approved_intake: Number(newProg.approved_intake) || 60,
      }
      const res = await api.post('/academic/programmes', payload)
      setProgrammes((prev) => [...prev, res.data])
      setShowProgModal(false)
      notify(`Programme ${newProg.name} added.`)
      setNewProg({
        programme_code: '',
        name: '',
        degree_type: 'Bachelor',
        degree_awarded: 'Bachelor',
        academic_level: 'UNDERGRADUATE',
        department_id: '',
        total_semesters: 8,
        duration_years: 4,
        approved_intake: 60,
      })
    } catch (err) {
      const msgText = errorMessage(err)
      setModalError(msgText)
      notify(msgText, 'error')
    }
  }

  const handleAddClass = async (e) => {
    e.preventDefault()
    setModalError('')
    try {
      const payload = {
        grade_level: newClass.grade_level,
        section: (newClass.section || 'A').toUpperCase(),
        academic_year: (newClass.academic_year || overview?.current_academic_year || '2025-26').replace(/^AY-/, ''),
        programme_id: newClass.programme_id || null,
        room_number: newClass.room_number || null,
        capacity: Number(newClass.capacity) || 40,
        class_teacher_name: newClass.class_teacher_name || null,
      }
      const res = await api.post('/academic/classes', payload)
      setClasses((prev) => [...prev, res.data])
      setShowClassModal(false)
      notify(`Class ${newClass.grade_level} Section ${newClass.section} added.`)
      setNewClass({
        grade_level: '',
        section: 'A',
        academic_year: '2025-26',
        room_number: '',
        capacity: 40,
        class_teacher_name: '',
      })
    } catch (err) {
      const msgText = errorMessage(err)
      setModalError(msgText)
      notify(msgText, 'error')
    }
  }

  const handleAddSubject = async (e) => {
    e.preventDefault()
    setModalError('')
    try {
      const payload = {
        subject_code: (newSubject.subject_code || '').toUpperCase(),
        subject_name: newSubject.subject_name,
        subject_name_hi: newSubject.subject_name_hi || newSubject.multilingual_name || null,
        category: (newSubject.category || 'CORE').toUpperCase(),
        applicable_to: newSubject.applicable_to || newSubject.grade_level || 'General',
        department_id: newSubject.department_id || null,
        programme_id: newSubject.programme_id || null,
        credits: Number(newSubject.credits) || 4.0,
        theory_hours: newSubject.is_practical ? 2 : 4,
        practical_hours: newSubject.is_practical ? 2 : 0,
        is_practical: Boolean(newSubject.is_practical),
      }
      const res = await api.post('/academic/subjects', payload)
      setSubjects((prev) => [...prev, res.data])
      setShowSubjectModal(false)
      notify(`Subject ${newSubject.subject_name} registered.`)
      setNewSubject({
        subject_code: '',
        subject_name: '',
        multilingual_name: '',
        subject_name_hi: '',
        credits: 4,
        is_practical: false,
        department_id: '',
        grade_level: 'Class 10',
        applicable_to: 'Class 10',
      })
    } catch (err) {
      const msgText = errorMessage(err)
      setModalError(msgText)
      notify(msgText, 'error')
    }
  }

  const handleAddEnrolment = async (e) => {
    e.preventDefault()
    setModalError('')
    try {
      const selectedYearDoc = years.find((y) => (y.id || y._id) === newEnrolment.academic_year_id)
      const yearLabel = selectedYearDoc?.year_label || (newEnrolment.academic_year || newEnrolment.academic_year_id || '2025-26').replace(/^AY-/, '')
      const selectedClass = classes.find((c) => (c.class_id || c.id) === newEnrolment.class_id)
      const payload = {
        student_id: newEnrolment.student_id,
        student_name: newEnrolment.student_name,
        roll_number: newEnrolment.roll_number || newEnrolment.enrolment_number || null,
        academic_year: yearLabel,
        class_id: selectedClass ? (selectedClass.class_id || selectedClass.id) : (newEnrolment.class_id || null),
        class_name: selectedClass ? `${selectedClass.grade_level} ${selectedClass.section}` : null,
        section: selectedClass ? selectedClass.section : 'A',
        remarks: newEnrolment.remarks || 'Regular enrolment.',
      }
      const res = await api.post('/academic/enrolments', payload)
      setEnrolments((prev) => [...prev, res.data])
      setShowEnrolModal(false)
      notify(`Enrolment for ${newEnrolment.student_name} recorded.`)
      setNewEnrolment({
        student_name: '',
        student_id: '',
        enrolment_number: '',
        roll_number: '',
        academic_year_id: 'AY-2025-26',
        academic_year: '2025-26',
        class_id: '',
      })
    } catch (err) {
      const msgText = errorMessage(err)
      setModalError(msgText)
      notify(msgText, 'error')
    }
  }

  const handlePromoteStudent = async (e) => {
    e.preventDefault()
    if (!selectedEnrolment) return
    setModalError('')
    const enrolmentId = selectedEnrolment.enrolment_id || selectedEnrolment.id
    try {
      const yearDoc = years.find((y) => (y.id || y._id) === promotionData.next_academic_year_id)
      const targetYear = yearDoc?.year_label || (promotionData.target_academic_year || promotionData.next_academic_year_id || '2026-27').replace(/^AY-/, '')
      const payload = {
        target_academic_year: targetYear,
        target_grade_or_semester: promotionData.target_grade_or_semester || promotionData.next_grade_level || 'Class 11',
        target_section: (promotionData.target_section || promotionData.next_section || 'A').toUpperCase(),
        promotion_status: 'PROMOTED',
        remarks: promotionData.remarks || promotionData.notes || 'Annual progression.',
      }
      const res = await api.post(
        `/academic/enrolments/${enrolmentId}/promote`,
        payload,
      )
      setEnrolments((prev) =>
        prev
          .map((enr) =>
            (enr.enrolment_id || enr.id) === enrolmentId
              ? { ...enr, status: 'PROMOTED', is_current: false }
              : enr,
          )
          .concat(res.data),
      )
      setShowPromotionModal(false)
      notify(
        `Student ${selectedEnrolment.student_name} promoted to ${payload.target_grade_or_semester} ${payload.target_section}. Previous history preserved.`,
      )
    } catch (err) {
      const msgText = errorMessage(err)
      setModalError(msgText)
      notify(msgText, 'error')
    }
  }

  const handleTransferSection = async (e) => {
    e.preventDefault()
    if (!selectedEnrolment) return
    setModalError('')
    const enrolmentId = selectedEnrolment.enrolment_id || selectedEnrolment.id
    try {
      const payload = {
        target_class_id: transferData.target_class_id || selectedEnrolment.class_id || `CLS-${selectedEnrolment.class_name || 'CLASS'}-${transferData.new_section || 'B'}`,
        target_section: (transferData.target_section || transferData.new_section || 'B').toUpperCase(),
        transfer_reason: transferData.transfer_reason || transferData.reason || 'Administrative section transfer.',
      }
      const res = await api.post(
        `/academic/enrolments/${enrolmentId}/transfer-section`,
        payload,
      )
      setEnrolments((prev) =>
        prev.map((enr) =>
          (enr.enrolment_id || enr.id) === enrolmentId
            ? res.data
            : enr,
        ),
      )
      setShowTransferModal(false)
      notify(
        `Student section transferred to Section ${payload.target_section}. Audit log updated.`,
      )
    } catch (err) {
      const msgText = errorMessage(err)
      setModalError(msgText)
      notify(msgText, 'error')
    }
  }

  const handleAddAssignment = async (e) => {
    e.preventDefault()
    setModalError('')
    try {
      const selectedSubj = subjects.find((s) => (s.subject_id || s.id || s.subject_code) === newAssignment.subject_id)
      const selectedCls = classes.find((c) => (c.class_id || c.id) === newAssignment.class_id)
      const roleMap = {
        'Primary Teacher': 'PRIMARY_INSTRUCTOR',
        'Assistant Teacher': 'ASSISTANT_INSTRUCTOR',
        'Guest Lecturer': 'GUEST_LECTURER',
        'Lab Instructor': 'LAB_INSTRUCTOR',
      }
      const payload = {
        teacher_id: newAssignment.teacher_id,
        teacher_name: newAssignment.teacher_name,
        subject_id: selectedSubj ? (selectedSubj.subject_id || selectedSubj.id) : newAssignment.subject_id,
        subject_name: selectedSubj ? selectedSubj.subject_name : (newAssignment.subject_name || 'Subject'),
        target_type: 'CLASS',
        target_id: selectedCls ? (selectedCls.class_id || selectedCls.id) : (newAssignment.class_id || 'CLS-DEFAULT'),
        target_label: selectedCls ? `${selectedCls.grade_level} ${selectedCls.section}` : (newAssignment.target_label || 'Class Section'),
        academic_year: (newAssignment.academic_year || overview?.current_academic_year || '2025-26').replace(/^AY-/, ''),
        role_in_course: roleMap[newAssignment.role_in_course] || (newAssignment.role_in_course || 'PRIMARY_INSTRUCTOR').toUpperCase().replace(/\s+/g, '_'),
      }
      const res = await api.post(
        '/academic/teacher-assignments',
        payload,
      )
      setAssignments((prev) => [...prev, res.data])
      setShowAssignModal(false)
      notify(
        `Teacher ${payload.teacher_name} allocated to subject.`,
      )
      setNewAssignment({
        teacher_name: '',
        teacher_id: '',
        subject_id: '',
        class_id: '',
        role_in_course: 'Primary Teacher',
        academic_year_id: 'AY-2025-26',
      })
    } catch (err) {
      const msgText = errorMessage(err)
      setModalError(msgText)
      notify(msgText, 'error')
    }
  }

  const handleDeleteAssignment = async (assignmentId) => {
    try {
      await api.delete(`/academic/teacher-assignments/${assignmentId}`)
      setAssignments((prev) => prev.filter((a) => (a.assignment_id || a.id) !== assignmentId))
      notify('Faculty allocation removed.')
    } catch (err) {
      notify(errorMessage(err), 'error')
    }
  }

  const handleAddEvent = async (e) => {
    e.preventDefault()
    setModalError('')
    try {
      const typeMap = {
        'holiday': 'HOLIDAY',
        'exam': 'EXAM',
        'admission': 'ADMISSION',
        'event': 'INSTITUTION_EVENT',
        'term_start': 'SEMESTER_START',
        'term_end': 'SEMESTER_END',
      }
      const rawType = (newEvent.event_type || 'holiday').toLowerCase()
      const evType = typeMap[rawType] || rawType.toUpperCase()
      const payload = {
        academic_year: (newEvent.academic_year || overview?.current_academic_year || '2025-26').replace(/^AY-/, ''),
        title: newEvent.title,
        description: newEvent.description || null,
        event_type: evType,
        start_date: newEvent.start_date,
        end_date: newEvent.end_date || newEvent.start_date,
        target_audience: 'ALL',
        is_holiday: evType === 'HOLIDAY',
        timezone: 'Asia/Kolkata',
      }
      const res = await api.post('/academic/calendar/events', payload)
      setCalendarEvents((prev) => [...prev, res.data])
      setShowEventModal(false)
      notify(`Calendar event "${payload.title}" published.`)
      setNewEvent({
        title: '',
        event_type: 'holiday',
        start_date: '',
        end_date: '',
        description: '',
      })
    } catch (err) {
      const msgText = errorMessage(err)
      setModalError(msgText)
      notify(msgText, 'error')
    }
  }

  const handleDeleteEvent = async (eventId) => {
    try {
      await api.delete(`/academic/calendar/events/${eventId}`)
      setCalendarEvents((prev) => prev.filter((e) => (e.event_id || e.id) !== eventId))
      notify('Calendar event removed.')
    } catch (err) {
      notify(errorMessage(err), 'error')
    }
  }

  // Filtered queries
  const filteredEvents =
    calendarFilter === 'all'
      ? calendarEvents
      : calendarEvents.filter((ev) => (ev.event_type || '').toLowerCase() === calendarFilter.toLowerCase())

  const filteredEnrolments = enrolments.filter((enr) => {
    const enrYear = enr.academic_year || enr.academic_year_id
    const matchesYear =
      filterYear === 'all' || enrYear === filterYear || enr.academic_year_id === filterYear
    const studentName = enr.student_name || ''
    const enrolNum = enr.roll_number || enr.enrolment_number || ''
    const matchesQuery =
      !searchQuery ||
      studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      enrolNum.toLowerCase().includes(searchQuery.toLowerCase())
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
                    openModal(setShowYearModal)
                  }}
                >
                  New Academic Year
                </Button>
                <Button
                  variant="secondary"
                  className="w-full text-xs"
                  onClick={() => {
                    setActiveTab('classes')
                    openModal(setShowClassModal)
                  }}
                >
                  New Class / Section
                </Button>
                <Button
                  variant="secondary"
                  className="w-full text-xs"
                  onClick={() => {
                    setActiveTab('enrolments')
                    openModal(setShowEnrolModal)
                  }}
                >
                  Enrol Student
                </Button>
                <Button
                  variant="secondary"
                  className="w-full text-xs"
                  onClick={() => {
                    setActiveTab('calendar')
                    openModal(setShowEventModal)
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
                onClick={() => openModal(setShowYearModal)}
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
                    <tr key={y.id || y._id} className="hover:bg-surface-2">
                      <td className="px-3 py-2.5 font-bold text-navy dark:text-white">
                        {y.year_label}
                      </td>
                      <td className="px-3 py-2.5 text-muted">
                        {y.start_date} to {y.end_date}
                      </td>
                      <td className="px-3 py-2.5 text-muted">
                        {(y.admission_start_date || y.admission_start) && (y.admission_end_date || y.admission_end)
                          ? `${y.admission_start_date || y.admission_start} to ${y.admission_end_date || y.admission_end}`
                          : 'Not configured'}
                      </td>
                      <td className="px-3 py-2.5">
                        {y.is_current ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                            Active Session
                          </span>
                        ) : y.status === 'ARCHIVED' || y.is_archived ? (
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
                        {!y.is_current && y.status !== 'ARCHIVED' && !y.is_archived && (
                          <button
                            type="button"
                            onClick={() => handleActivateYear(y.id || y._id)}
                            className="text-xs font-semibold text-bright-blue hover:underline"
                          >
                            Set Active
                          </button>
                        )}
                        {y.status !== 'ARCHIVED' && !y.is_archived && (
                          <button
                            type="button"
                            onClick={() => handleArchiveYear(y.id || y._id)}
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
                onClick={() => openModal(setShowTermModal)}
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
                    <tr key={t.term_id || t.id} className="hover:bg-surface-2">
                      <td className="px-3 py-2 font-medium text-navy dark:text-white">
                        {t.name || t.term_name}
                      </td>
                      <td className="px-3 py-2 uppercase text-muted">{t.term_type}</td>
                      <td className="px-3 py-2 text-muted">{t.term_number ? `Term ${t.term_number}` : '-'}</td>
                      <td className="px-3 py-2 text-muted">{t.start_date}</td>
                      <td className="px-3 py-2 text-muted">{t.end_date}</td>
                      <td className="px-3 py-2 text-muted font-mono">{t.academic_year || t.academic_year_id}</td>
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
                onClick={() => openModal(setShowDeptModal)}
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
                    <tr key={d.department_id || d.id} className="hover:bg-surface-2">
                      <td className="px-3 py-2 font-mono font-bold text-navy dark:text-bright-blue">
                        {d.department_code || d.dept_code}
                      </td>
                      <td className="px-3 py-2 font-medium text-navy dark:text-white">
                        {d.name}
                      </td>
                      <td className="px-3 py-2 text-muted">{d.head_of_department_name || d.head_of_department || '-'}</td>
                      <td className="px-3 py-2 text-muted font-mono text-[11px]">{d.contact_email || d.email || '-'}</td>
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
                onClick={() => openModal(setShowProgModal)}
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
                    <th className="px-3 py-2 border-b border-line">Credits / Intake</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {programmes.map((p) => (
                    <tr key={p.programme_id || p.id} className="hover:bg-surface-2">
                      <td className="px-3 py-2 font-mono font-bold text-navy dark:text-bright-blue">
                        {p.programme_code}
                      </td>
                      <td className="px-3 py-2 font-medium text-navy dark:text-white">
                        {p.name}
                      </td>
                      <td className="px-3 py-2 text-muted">{p.degree_awarded || p.academic_level || p.degree_type}</td>
                      <td className="px-3 py-2 text-muted">{p.total_semesters} Semesters</td>
                      <td className="px-3 py-2 text-muted">{p.approved_intake ? `${p.approved_intake} Intake` : `${p.total_credits || 160} Credits`}</td>
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
              onClick={() => openModal(setShowClassModal)}
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
                  <tr key={c.class_id || c.id || `${c.grade_level}-${c.section}`} className="hover:bg-surface-2">
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
              onClick={() => openModal(setShowSubjectModal)}
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
                  <tr key={s.subject_id || s.id || s.subject_code} className="hover:bg-surface-2">
                    <td className="px-3 py-2 font-mono font-bold text-navy dark:text-bright-blue">
                      {s.subject_code}
                    </td>
                    <td className="px-3 py-2 font-medium text-navy dark:text-white">
                      {s.subject_name}
                    </td>
                    <td className="px-3 py-2 text-muted">{s.subject_name_hi || s.multilingual_name || '-'}</td>
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
                    <td className="px-3 py-2 text-muted">{s.applicable_to || s.grade_level || '-'}</td>
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
              onClick={() => openModal(setShowEnrolModal)}
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
                <option key={y.id || y._id} value={y.id || y._id}>
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
                  <tr key={enr.enrolment_id || enr.id} className="hover:bg-surface-2">
                    <td className="px-3 py-2 font-mono font-bold text-navy dark:text-bright-blue">
                      {enr.roll_number || enr.enrolment_number || '-'}
                    </td>
                    <td className="px-3 py-2 font-medium text-navy dark:text-white">
                      {enr.student_name}
                    </td>
                    <td className="px-3 py-2 text-muted font-mono">{enr.class_name || enr.class_id || '-'}</td>
                    <td className="px-3 py-2 text-muted">{enr.academic_year || enr.academic_year_id}</td>
                    <td className="px-3 py-2 text-muted">{enr.enrolled_date || enr.enrolment_date || '-'}</td>
                    <td className="px-3 py-2">
                      {String(enr.status || '').toUpperCase() === 'ACTIVE' ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                          Active
                        </span>
                      ) : String(enr.status || '').toUpperCase() === 'PROMOTED' ? (
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
                            onClick={() => openModal(setShowPromotionModal, enr)}
                            className="text-xs font-semibold text-bright-blue hover:underline"
                          >
                            Promote
                          </button>
                          <button
                            type="button"
                            onClick={() => openModal(setShowTransferModal, enr)}
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
              onClick={() => openModal(setShowAssignModal)}
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
                  <tr key={asg.assignment_id || asg.id} className="hover:bg-surface-2">
                    <td className="px-3 py-2 font-bold text-navy dark:text-white">
                      {asg.teacher_name}
                    </td>
                    <td className="px-3 py-2 font-mono text-muted">{asg.subject_name || asg.subject_id}</td>
                    <td className="px-3 py-2 font-mono text-muted">{asg.target_label || asg.class_id}</td>
                    <td className="px-3 py-2">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-surface-2 text-navy border border-line">
                        {asg.role_in_course}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-muted">{asg.academic_year || asg.academic_year_id}</td>
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => handleDeleteAssignment(asg.assignment_id || asg.id)}
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
              onClick={() => openModal(setShowEventModal)}
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
                key={ev.event_id || ev.id}
                className="p-4 rounded-md border border-line bg-surface-2 flex items-start justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-navy dark:text-white">
                      {ev.title}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                        (ev.event_type || '').toLowerCase() === 'holiday'
                          ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                          : (ev.event_type || '').toLowerCase() === 'exam'
                            ? 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300'
                            : (ev.event_type || '').toLowerCase() === 'admission'
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
                  onClick={() => handleDeleteEvent(ev.event_id || ev.id)}
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
            {modalError && (
              <div role="alert" className="p-3 rounded-md border text-xs font-medium bg-danger-surface text-danger-strong border-danger/30">
                {modalError}
              </div>
            )}
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
                  onClick={() => {
                    setShowYearModal(false)
                    setModalError('')
                  }}
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
            {modalError && (
              <div role="alert" className="p-3 rounded-md border text-xs font-medium bg-danger-surface text-danger-strong border-danger/30">
                {modalError}
              </div>
            )}
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
              {years.length > 0 && (
                <div>
                  <label className="block text-muted mb-1 font-medium">Academic Year</label>
                  <select
                    value={newTerm.academic_year || years[0]?.year_label || ''}
                    onChange={(e) =>
                      setNewTerm({ ...newTerm, academic_year: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  >
                    {years.map((y) => (
                      <option key={y.id} value={y.year_label}>
                        {y.year_label}
                      </option>
                    ))}
                  </select>
                </div>
              )}
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
                  onClick={() => {
                    setShowTermModal(false)
                    setModalError('')
                  }}
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
            {modalError && (
              <div role="alert" className="p-3 rounded-md border text-xs font-medium bg-danger-surface text-danger-strong border-danger/30">
                {modalError}
              </div>
            )}
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
                  onClick={() => {
                    setShowDeptModal(false)
                    setModalError('')
                  }}
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
            {modalError && (
              <div role="alert" className="p-3 rounded-md border text-xs font-medium bg-danger-surface text-danger-strong border-danger/30">
                {modalError}
              </div>
            )}
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
              {departments.length > 0 && (
                <div>
                  <label className="block text-muted mb-1 font-medium">Department</label>
                  <select
                    value={newProg.department_id || departments[0]?.id || ''}
                    onChange={(e) =>
                      setNewProg({ ...newProg, department_id: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  >
                    {departments.map((d) => (
                      <option key={d.id || d.department_code} value={d.id || d.department_code}>
                        {d.department_code ? `${d.department_code} - ` : ''}{d.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
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
                  onClick={() => {
                    setShowProgModal(false)
                    setModalError('')
                  }}
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
            {modalError && (
              <div role="alert" className="p-3 rounded-md border text-xs font-medium bg-danger-surface text-danger-strong border-danger/30">
                {modalError}
              </div>
            )}
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
              {programmes.length > 0 && (
                <div>
                  <label className="block text-muted mb-1 font-medium">Programme (Optional)</label>
                  <select
                    value={newClass.programme_id || ''}
                    onChange={(e) =>
                      setNewClass({ ...newClass, programme_id: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  >
                    <option value="">None / Standalone Class</option>
                    {programmes.map((p) => (
                      <option key={p.id || p.programme_code} value={p.id || p.programme_code}>
                        {p.programme_code} - {p.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
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
                  onClick={() => {
                    setShowClassModal(false)
                    setModalError('')
                  }}
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
            {modalError && (
              <div role="alert" className="p-3 rounded-md border text-xs font-medium bg-danger-surface text-danger-strong border-danger/30">
                {modalError}
              </div>
            )}
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
              {departments.length > 0 && (
                <div>
                  <label className="block text-muted mb-1 font-medium">Department (Optional)</label>
                  <select
                    value={newSubject.department_id || ''}
                    onChange={(e) =>
                      setNewSubject({ ...newSubject, department_id: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-line rounded-md bg-surface text-navy dark:text-white"
                  >
                    <option value="">None / General</option>
                    {departments.map((d) => (
                      <option key={d.id || d.department_code} value={d.id || d.department_code}>
                        {d.department_code ? `${d.department_code} - ` : ''}{d.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
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
                  onClick={() => {
                    setShowSubjectModal(false)
                    setModalError('')
                  }}
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
            {modalError && (
              <div role="alert" className="p-3 rounded-md border text-xs font-medium bg-danger-surface text-danger-strong border-danger/30">
                {modalError}
              </div>
            )}
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
                  onClick={() => {
                    setShowEnrolModal(false)
                    setModalError('')
                  }}
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
            {modalError && (
              <div role="alert" className="p-3 rounded-md border text-xs font-medium bg-danger-surface text-danger-strong border-danger/30">
                {modalError}
              </div>
            )}
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
                  onClick={() => {
                    setShowPromotionModal(false)
                    setModalError('')
                  }}
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
            {modalError && (
              <div role="alert" className="p-3 rounded-md border text-xs font-medium bg-danger-surface text-danger-strong border-danger/30">
                {modalError}
              </div>
            )}
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
                  onClick={() => {
                    setShowTransferModal(false)
                    setModalError('')
                  }}
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
            {modalError && (
              <div role="alert" className="p-3 rounded-md border text-xs font-medium bg-danger-surface text-danger-strong border-danger/30">
                {modalError}
              </div>
            )}
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
                  onClick={() => {
                    setShowAssignModal(false)
                    setModalError('')
                  }}
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
            {modalError && (
              <div role="alert" className="p-3 rounded-md border text-xs font-medium bg-danger-surface text-danger-strong border-danger/30">
                {modalError}
              </div>
            )}
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
                  onClick={() => {
                    setShowEventModal(false)
                    setModalError('')
                  }}
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
