import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api, errorMessage } from '../../services/api'
import { useAuth } from '../../hooks/useAuth'
import { Badge, Button, Spinner } from './index'

export default function StudentAcademicSelectionWizard({ isOpen, onClose, onSuccess }) {
  const { t } = useTranslation()
  const { login } = useAuth()
  const navigate = useNavigate()

  // Steps: 1: Education Type, 2: Academic Details, 3: Confirmation
  const [step, setStep] = useState(1)
  const [educationType, setEducationType] = useState('school') // 'school' | 'college'

  // Options from backend
  const [contextData, setContextData] = useState({ schools: [], colleges: [] })
  const [loadingContext, setLoadingContext] = useState(false)
  const [fetchError, setFetchError] = useState('')

  // Selections
  const [selectedInstId, setSelectedInstId] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  // School specifics
  const [selectedClass, setSelectedClass] = useState('')
  const [selectedSection, setSelectedSection] = useState('')

  // College specifics
  const [selectedProgramId, setSelectedProgramId] = useState('')
  const [selectedSemester, setSelectedSemester] = useState('')

  // Submission state
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  // Fetch academic options when modal opens
  useEffect(() => {
    if (!isOpen) return

    setStep(1)
    setSubmitError('')
    setFetchError('')
    setSearchQuery('')
    setLoadingContext(true)

    api
      .get('/auth/demo-academic-context')
      .then((res) => {
        const data = res.data || {}
        setContextData({
          schools: Array.isArray(data.schools) ? data.schools : [],
          colleges: Array.isArray(data.colleges) ? data.colleges : [],
        })
      })
      .catch((err) => {
        setFetchError(errorMessage(err, 'Could not load demo academic options.'))
      })
      .finally(() => {
        setLoadingContext(false)
      })
  }, [isOpen])

  // Reset dependent selections when education type or institution changes
  useEffect(() => {
    const list = educationType === 'school' ? contextData.schools : contextData.colleges
    if (list.length > 0) {
      const first = list[0]
      setSelectedInstId(first.institution_id)

      if (educationType === 'school') {
        const firstClass = first.classes?.[0]
        setSelectedClass(firstClass?.class_name || 'Class 10')
        setSelectedSection(firstClass?.sections?.[0] || 'A')
      } else {
        const firstCourse = first.courses?.[0]
        setSelectedProgramId(firstCourse?.program_id || '')
        setSelectedSemester(firstCourse?.semesters?.[0] || 'Semester 1')
      }
    }
  }, [educationType, contextData])

  // Handle institution change
  const handleInstitutionChange = (instId) => {
    setSelectedInstId(instId)
    if (educationType === 'school') {
      const school = contextData.schools.find((s) => s.institution_id === instId)
      const firstClass = school?.classes?.[0]
      setSelectedClass(firstClass?.class_name || '')
      setSelectedSection(firstClass?.sections?.[0] || 'A')
    } else {
      const college = contextData.colleges.find((c) => c.institution_id === instId)
      const firstCourse = college?.courses?.[0]
      setSelectedProgramId(firstCourse?.program_id || '')
      setSelectedSemester(firstCourse?.semesters?.[0] || 'Semester 1')
    }
  }

  // Handle course change for college
  const handleProgramChange = (progId) => {
    setSelectedProgramId(progId)
    const college = contextData.colleges.find((c) => c.institution_id === selectedInstId)
    const course = college?.courses?.find((p) => p.program_id === progId)
    setSelectedSemester(course?.semesters?.[0] || 'Semester 1')
  }

  // Handle class change for school
  const handleClassChange = (className) => {
    setSelectedClass(className)
    const school = contextData.schools.find((s) => s.institution_id === selectedInstId)
    const cls = school?.classes?.find((c) => c.class_name === className)
    setSelectedSection(cls?.sections?.[0] || 'A')
  }

  // Active institution reference
  const currentInstitution =
    educationType === 'school'
      ? contextData.schools.find((s) => s.institution_id === selectedInstId)
      : contextData.colleges.find((c) => c.institution_id === selectedInstId)

  // Filtered institutions based on search query
  const filteredInstitutions = (
    educationType === 'school' ? contextData.schools : contextData.colleges
  ).filter((inst) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      inst.name.toLowerCase().includes(q) ||
      inst.city.toLowerCase().includes(q) ||
      inst.state.toLowerCase().includes(q) ||
      inst.institution_id.toLowerCase().includes(q)
    )
  })

  // Submit academic context demo login
  const handleConfirmAndLogin = async () => {
    setSubmitting(true)
    setSubmitError('')

    const payload = {
      role: 'student',
      education_type: educationType,
      institution_id: selectedInstId,
      ...(educationType === 'school'
        ? { class_name: selectedClass, section: selectedSection }
        : { program_id: selectedProgramId, semester: selectedSemester }),
    }

    try {
      const res = await api.post('/auth/demo-login', payload)
      if (res?.data?.access_token) {
        login(res.data)
        if (onSuccess) {
          onSuccess(res.data)
        } else {
          onClose()
          navigate('/me', { replace: true })
        }
      } else {
        throw new Error('No access token received from demo session.')
      }
    } catch (caught) {
      setSubmitError(errorMessage(caught, 'Failed to establish demo student session.'))
    } finally {
      setSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="wizard-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/60"
      onKeyDown={(e) => {
        if (e.key === 'Escape' && !submitting) onClose()
      }}
    >
      <div className="w-full max-w-xl bg-surface border border-line-strong rounded-lg shadow-sm overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Top Header */}
        <div className="px-6 py-4 border-b border-line bg-surface-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-accent" />
            <h2 id="wizard-title" className="text-base font-bold text-ink m-0">
              Student Academic Onboarding
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="text-muted hover:text-ink text-sm font-semibold p-1.5 rounded hover:bg-surface-3 transition cursor-pointer"
            aria-label="Close dialog"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Step Progress Tracker */}
        <div className="px-6 pt-4 pb-2 bg-surface border-b border-line">
          <div className="flex items-center justify-between text-xs text-muted mb-2">
            <span className={step >= 1 ? 'font-bold text-brand' : ''}>1. Education Type</span>
            <span>&rarr;</span>
            <span className={step >= 2 ? 'font-bold text-brand' : ''}>2. Academic Details</span>
            <span>&rarr;</span>
            <span className={step >= 3 ? 'font-bold text-brand' : ''}>3. Confirmation</span>
          </div>
          <div className="w-full bg-surface-2 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-brand h-full transition-all duration-300"
              style={{ width: step === 1 ? '33.3%' : step === 2 ? '66.6%' : '100%' }}
            />
          </div>
        </div>

        {/* Modal Body with Scroll */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {loadingContext && (
            <div className="py-12 flex flex-col items-center justify-center space-y-3">
              <Spinner label="Loading demo institutions and courses..." />
              <p className="text-xs text-muted m-0">Connecting to national academic catalog...</p>
            </div>
          )}

          {!loadingContext && fetchError && (
            <div className="p-4 rounded border border-danger/30 bg-danger-surface text-danger-strong text-sm">
              <p className="font-semibold m-0">{fetchError}</p>
              <button
                type="button"
                onClick={() => setStep(1)}
                className="mt-2 text-xs font-bold text-danger underline cursor-pointer"
              >
                Retry
              </button>
            </div>
          )}

          {!loadingContext && !fetchError && (
            <>
              {/* STEP 1: EDUCATION TYPE */}
              {step === 1 && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-bold text-ink m-0">
                      Are you a School student or a College student?
                    </h3>
                    <p className="text-xs text-muted mt-1 m-0">
                      Select your educational institution category to load relevant classes, semesters, and curriculum records.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                    {/* School Option */}
                    <button
                      type="button"
                      onClick={() => setEducationType('school')}
                      className={`p-5 rounded-lg border text-left transition cursor-pointer flex flex-col justify-between space-y-3 ${
                        educationType === 'school'
                          ? 'border-brand bg-brand/5 ring-1 ring-brand'
                          : 'border-line bg-surface hover:bg-surface-2'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="p-2 rounded bg-brand/10 text-brand">
                          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                          </svg>
                        </span>
                        {educationType === 'school' && (
                          <span className="w-3 h-3 rounded-full bg-brand" />
                        )}
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-ink m-0">School Student</h4>
                        <p className="text-xs text-muted mt-1 m-0">
                          Primary, Secondary, and Senior Secondary (Class 1 to 12).
                        </p>
                      </div>
                      <Badge className="bg-surface self-start text-[10px]">K-12 Boards</Badge>
                    </button>

                    {/* College Option */}
                    <button
                      type="button"
                      onClick={() => setEducationType('college')}
                      className={`p-5 rounded-lg border text-left transition cursor-pointer flex flex-col justify-between space-y-3 ${
                        educationType === 'college'
                          ? 'border-brand bg-brand/5 ring-1 ring-brand'
                          : 'border-line bg-surface hover:bg-surface-2'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="p-2 rounded bg-accent/15 text-accent-strong">
                          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
                          </svg>
                        </span>
                        {educationType === 'college' && (
                          <span className="w-3 h-3 rounded-full bg-brand" />
                        )}
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-ink m-0">College Student</h4>
                        <p className="text-xs text-muted mt-1 m-0">
                          Higher Education, Engineering, Polytechnics, and Universities.
                        </p>
                      </div>
                      <Badge className="bg-surface self-start text-[10px]">UG / PG / Diploma</Badge>
                    </button>
                  </div>
                </div>
              )}

              {/* STEP 2: ACADEMIC DETAILS */}
              {step === 2 && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-bold text-ink m-0">
                      {educationType === 'school' ? 'Select School & Class' : 'Select College & Course'}
                    </h3>
                    <p className="text-xs text-muted mt-1 m-0">
                      Choose from the available institutions and academic programs supported in the demo dataset.
                    </p>
                  </div>

                  {/* Institution Selection with Search Filter */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-ink block">
                      {educationType === 'school' ? 'School / Institution' : 'College / Institution'}
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        placeholder="Search institution by name, city, or code..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full text-xs px-3 py-2 border border-line rounded-md bg-surface mb-2 focus:ring-1 focus:ring-brand focus:border-brand"
                      />
                    </div>
                    <select
                      value={selectedInstId}
                      onChange={(e) => handleInstitutionChange(e.target.value)}
                      className="w-full text-sm px-3 py-2 border border-line rounded-md bg-surface focus:ring-1 focus:ring-brand focus:border-brand"
                    >
                      {filteredInstitutions.length === 0 ? (
                        <option value="">No matching institutions found</option>
                      ) : (
                        filteredInstitutions.map((inst) => (
                          <option key={inst.institution_id} value={inst.institution_id}>
                            {inst.name} ({inst.city}, {inst.state}) - [{inst.institution_id}]
                          </option>
                        ))
                      )}
                    </select>
                  </div>

                  {/* School Student Context Controls */}
                  {educationType === 'school' && currentInstitution && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                      <div className="space-y-1.5">
                        <label className="text-xs font-bold text-ink block">Class Level</label>
                        <select
                          value={selectedClass}
                          onChange={(e) => handleClassChange(e.target.value)}
                          className="w-full text-sm px-3 py-2 border border-line rounded-md bg-surface focus:ring-1 focus:ring-brand focus:border-brand"
                        >
                          {currentInstitution.classes?.map((cls) => (
                            <option key={cls.class_name} value={cls.class_name}>
                              {cls.class_name}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-xs font-bold text-ink block">Section</label>
                        <select
                          value={selectedSection}
                          onChange={(e) => setSelectedSection(e.target.value)}
                          className="w-full text-sm px-3 py-2 border border-line rounded-md bg-surface focus:ring-1 focus:ring-brand focus:border-brand"
                        >
                          {currentInstitution.classes
                            ?.find((c) => c.class_name === selectedClass)
                            ?.sections?.map((sec) => (
                              <option key={sec} value={sec}>
                                Section {sec}
                              </option>
                            ))}
                        </select>
                      </div>
                    </div>
                  )}

                  {/* College Student Context Controls */}
                  {educationType === 'college' && currentInstitution && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                      <div className="space-y-1.5 sm:col-span-2">
                        <label className="text-xs font-bold text-ink block">Course / Degree Programme</label>
                        <select
                          value={selectedProgramId}
                          onChange={(e) => handleProgramChange(e.target.value)}
                          className="w-full text-sm px-3 py-2 border border-line rounded-md bg-surface focus:ring-1 focus:ring-brand focus:border-brand"
                        >
                          {currentInstitution.courses?.map((course) => (
                            <option key={course.program_id} value={course.program_id}>
                              {course.program_name} ({course.level})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="space-y-1.5 sm:col-span-2">
                        <label className="text-xs font-bold text-ink block">Academic Semester</label>
                        <select
                          value={selectedSemester}
                          onChange={(e) => setSelectedSemester(e.target.value)}
                          className="w-full text-sm px-3 py-2 border border-line rounded-md bg-surface focus:ring-1 focus:ring-brand focus:border-brand"
                        >
                          {currentInstitution.courses
                            ?.find((p) => p.program_id === selectedProgramId)
                            ?.semesters?.map((sem) => (
                              <option key={sem} value={sem}>
                                {sem}
                              </option>
                            ))}
                        </select>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* STEP 3: CONFIRMATION & REVIEW */}
              {step === 3 && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-bold text-ink m-0">Confirm Demo Student Profile</h3>
                    <p className="text-xs text-muted mt-1 m-0">
                      Your demo session will be created with verified academic records matching your chosen context.
                    </p>
                  </div>

                  {submitError && (
                    <div className="p-3.5 rounded border border-danger/30 bg-danger-surface text-danger-strong text-sm">
                      <p className="font-semibold m-0">{submitError}</p>
                      <button
                        type="button"
                        onClick={() => setStep(2)}
                        className="mt-1 text-xs font-bold text-danger underline cursor-pointer"
                      >
                        Change academic selection
                      </button>
                    </div>
                  )}

                  {/* Confirmation Summary Card */}
                  <div className="border border-line rounded-lg bg-surface-2 p-5 space-y-4">
                    <div className="flex items-center justify-between border-b border-line pb-3">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-accent-strong">
                          {educationType === 'school' ? 'K-12 School Student' : 'Higher Education Student'}
                        </span>
                        <h4 className="text-base font-extrabold text-ink m-0 mt-0.5">
                          {educationType === 'school'
                            ? `Aarav Sharma (${selectedClass} - Sec ${selectedSection})`
                            : `Aarav Sharma (${selectedProgramId} - ${selectedSemester})`}
                        </h4>
                      </div>
                      <Badge className="bg-success-surface text-success-strong">Verified Demo Profile</Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-muted block">Institution:</span>
                        <span className="font-semibold text-ink">{currentInstitution?.name}</span>
                      </div>
                      <div>
                        <span className="text-muted block">Institution Code:</span>
                        <span className="font-mono text-ink font-semibold">{selectedInstId}</span>
                      </div>
                      <div>
                        <span className="text-muted block">
                          {educationType === 'school' ? 'Class & Section:' : 'Course & Semester:'}
                        </span>
                        <span className="font-semibold text-brand">
                          {educationType === 'school'
                            ? `${selectedClass} - Section ${selectedSection}`
                            : `${selectedProgramId} - ${selectedSemester}`}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted block">Session / Academic Year:</span>
                        <span className="font-semibold text-ink">
                          {educationType === 'school' ? '2025-26' : '2024-25'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <p className="text-[11px] text-muted m-0">
                    Entering the dashboard gives you complete access to view this student's APAAR ID badge, attendance history, timetable, and credential verification tokens.
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Action Footer */}
        <div className="px-6 py-4 border-t border-line bg-surface-2 flex items-center justify-between">
          {step > 1 ? (
            <button
              type="button"
              disabled={submitting}
              onClick={() => setStep((s) => s - 1)}
              className="btn btn-outline text-xs px-4 py-2 cursor-pointer"
            >
              &larr; Back
            </button>
          ) : (
            <button
              type="button"
              disabled={submitting}
              onClick={onClose}
              className="btn btn-ghost text-xs px-4 py-2 text-muted hover:text-ink cursor-pointer"
            >
              Cancel
            </button>
          )}

          {step < 3 ? (
            <Button
              variant="brand"
              onClick={() => setStep((s) => s + 1)}
              disabled={
                loadingContext ||
                Boolean(fetchError) ||
                (step === 2 && !selectedInstId)
              }
              className="text-xs px-5 py-2 cursor-pointer"
            >
              Continue &rarr;
            </Button>
          ) : (
            <Button
              variant="accent"
              onClick={handleConfirmAndLogin}
              disabled={submitting || !selectedInstId}
              className="text-xs px-5 py-2 font-bold cursor-pointer"
            >
              {submitting ? 'Creating Demo Session...' : 'Enter Student Dashboard'}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
