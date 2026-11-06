/**
 * Navigation Configuration and Permission Mapping.
 * Shared across all user roles and application modules.
 */

import { PERMISSIONS } from '../../utils/permissions'

export const NAVIGATION_REGISTRY = [
  // Common / Dashboard
  {
    id: 'dashboard-national',
    to: '/dashboard',
    label: 'nav.universityDashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.VIEW_NATIONAL_DASHBOARD,
  },
  {
    id: 'dashboard-institution',
    to: '/institution',
    label: 'nav.dashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.VIEW_INSTITUTION_DASHBOARD,
  },
  {
    id: 'dashboard-student',
    to: '/me',
    label: 'nav.dashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
  },
  {
    id: 'dashboard-parent',
    to: '/parent',
    label: 'nav.dashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.VIEW_PARENT_PORTAL,
  },
  {
    id: 'dashboard-teacher',
    to: '/teacher',
    label: 'nav.dashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.RECORD_ATTENDANCE,
  },

  // Academic Setup & Classes
  {
    id: 'institutions-registry',
    to: '/institutions',
    label: 'nav.institutions',
    icon: 'institutions',
    permission: PERMISSIONS.VIEW_COMPLIANCE_MATRIX,
  },
  {
    id: 'academic-setup',
    to: '/academic',
    label: 'nav.academics',
    icon: 'academic',
    permission: PERMISSIONS.MANAGE_ACADEMIC_SETUP,
  },
  {
    id: 'teacher-classes',
    to: '/teacher',
    label: 'nav.classes',
    icon: 'academic',
    permission: PERMISSIONS.RECORD_ATTENDANCE,
  },
  {
    id: 'student-academics',
    to: '/me/academics',
    label: 'nav.academics',
    icon: 'academic',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
  },

  // Student Register & Admissions
  {
    id: 'students-register',
    to: '/students',
    label: 'nav.students',
    icon: 'students',
    permission: PERMISSIONS.VIEW_STUDENT_REGISTER,
  },

  // Attendance & Timetable
  {
    id: 'attendance-record',
    to: '/teacher',
    label: 'nav.attendance',
    icon: 'attendance',
    permission: PERMISSIONS.RECORD_ATTENDANCE,
  },
  {
    id: 'student-attendance',
    to: '/me/attendance',
    label: 'nav.attendance',
    icon: 'attendance',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
  },
  {
    id: 'student-timetable',
    to: '/me/timetable',
    label: 'nav.timetable',
    icon: 'timetable',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
  },

  // Assignments
  {
    id: 'student-assignments',
    to: '/me/assignments',
    label: 'nav.assignments',
    icon: 'assignments',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
  },

  // Examinations & Results
  {
    id: 'assessments-admin',
    to: '/assessments',
    label: 'nav.examinations',
    icon: 'examinations',
    permission: PERMISSIONS.VIEW_RESULTS,
  },
  {
    id: 'student-results',
    to: '/me/results',
    label: 'nav.results',
    icon: 'results',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
  },

  // Documents & Credentials
  {
    id: 'student-documents',
    to: '/me/id-card',
    label: 'nav.documents',
    icon: 'documents',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
  },
  {
    id: 'upload-csv',
    to: '/upload',
    label: 'nav.upload',
    icon: 'documents',
    permission: PERMISSIONS.IMPORT_CSV,
  },

  // Opportunities & Library
  {
    id: 'library-common',
    to: '/library',
    label: 'nav.library',
    icon: 'library',
    permission: null, // Open to all authenticated users
  },
  {
    id: 'opportunities-common',
    to: '/opportunities',
    label: 'nav.opportunities',
    icon: 'opportunities',
    permission: null, // Open to all authenticated users
  },

  // Announcements & Notices
  {
    id: 'announcements-view',
    to: '/announcements',
    label: 'nav.announcements',
    icon: 'announcements',
    permission: PERMISSIONS.VIEW_ANNOUNCEMENTS,
  },

  // Reports
  {
    id: 'reports-export',
    to: '/reports',
    label: 'nav.reports',
    icon: 'reports',
    permission: PERMISSIONS.EXPORT_REPORTS,
  },

  // Notifications Centre
  {
    id: 'notifications-centre',
    to: '/notifications',
    label: 'nav.notifications',
    icon: 'notifications',
    permission: null, // Open to all authenticated users
    badgeKey: 'unread_notifications',
  },

  // Profile & Account Settings
  {
    id: 'profile-settings',
    to: '/profile',
    label: 'nav.profile',
    icon: 'profile',
    permission: null, // Open to all authenticated users
  },
]

export const ROLE_DEFAULT_NAVIGATIONS = {
  student: [
    { to: '/me', label: 'nav.dashboard', icon: 'dashboard' },
    { to: '/me/academics', label: 'nav.academics', icon: 'academic' },
    { to: '/me/attendance', label: 'nav.attendance', icon: 'attendance' },
    { to: '/me/timetable', label: 'nav.timetable', icon: 'timetable' },
    { to: '/me/assignments', label: 'nav.assignments', icon: 'assignments' },
    { to: '/me/results', label: 'nav.examinations', icon: 'examinations' },
    { to: '/me/results', label: 'nav.results', icon: 'results' },
    { to: '/me/id-card', label: 'nav.documents', icon: 'documents' },
    { to: '/library', label: 'nav.library', icon: 'library' },
    { to: '/opportunities', label: 'nav.opportunities', icon: 'opportunities' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications', hasBadge: true },
    { to: '/profile', label: 'nav.profile', icon: 'profile' },
  ],
  parent: [
    { to: '/parent', label: 'nav.dashboard', icon: 'dashboard' },
    { to: '/parent', label: 'nav.children', icon: 'students' },
    { to: '/parent', label: 'nav.attendance', icon: 'attendance' },
    { to: '/assessments', label: 'nav.results', icon: 'results' },
    { to: '/announcements', label: 'nav.announcements', icon: 'announcements' },
    { to: '/parent', label: 'nav.meetings', icon: 'timetable' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications', hasBadge: true },
    { to: '/profile', label: 'nav.profile', icon: 'profile' },
  ],
  teacher: [
    { to: '/teacher', label: 'nav.dashboard', icon: 'dashboard' },
    { to: '/teacher', label: 'nav.classes', icon: 'academic' },
    { to: '/teacher', label: 'nav.attendance', icon: 'attendance' },
    { to: '/teacher', label: 'nav.assignments', icon: 'assignments' },
    { to: '/assessments', label: 'nav.examinations', icon: 'examinations' },
    { to: '/assessments', label: 'nav.results', icon: 'results' },
    { to: '/students', label: 'nav.students', icon: 'students' },
    { to: '/announcements', label: 'nav.announcements', icon: 'announcements' },
    { to: '/profile', label: 'nav.profile', icon: 'profile' },
  ],
  institution_admin: [
    { to: '/institution', label: 'nav.dashboard', icon: 'dashboard' },
    { to: '/students', label: 'nav.students', icon: 'students' },
    { to: '/teacher', label: 'nav.staff', icon: 'staff' },
    { to: '/students', label: 'nav.admissions', icon: 'admissions' },
    { to: '/academic', label: 'nav.academics', icon: 'academic' },
    { to: '/teacher', label: 'nav.attendance', icon: 'attendance' },
    { to: '/assessments', label: 'nav.examinations', icon: 'examinations' },
    { to: '/reports', label: 'nav.reports', icon: 'reports' },
    { to: '/upload', label: 'nav.documents', icon: 'documents' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications', hasBadge: true },
    { to: '/profile', label: 'nav.settings', icon: 'profile' },
  ],
  university_admin: [
    { to: '/dashboard', label: 'nav.universityDashboard', icon: 'dashboard' },
    { to: '/institutions', label: 'nav.institutions', icon: 'institutions' },
    { to: '/academic', label: 'nav.departments', icon: 'academic' },
    { to: '/academic', label: 'nav.programmes', icon: 'academic' },
    { to: '/students', label: 'nav.students', icon: 'students' },
    { to: '/assessments', label: 'nav.examinations', icon: 'examinations' },
    { to: '/assessments', label: 'nav.results', icon: 'results' },
    { to: '/reports', label: 'nav.reports', icon: 'reports' },
    { to: '/profile', label: 'nav.settings', icon: 'profile' },
  ],
}
