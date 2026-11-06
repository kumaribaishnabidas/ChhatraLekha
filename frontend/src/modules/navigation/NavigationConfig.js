/**
 * Navigation Configuration and Permission Mapping.
 * Shared across all user roles and application modules.
 */

import { PERMISSIONS } from '../../utils/permissions'

export const NAVIGATION_GROUPS = [
  { id: 'dashboard', label: 'nav.dashboard' },
  { id: 'profile', label: 'nav.profile' },
  { id: 'academics', label: 'nav.academics' },
  { id: 'attendance', label: 'nav.attendance' },
  { id: 'timetable', label: 'nav.timetable' },
  { id: 'assignments', label: 'nav.assignments' },
  { id: 'examinations', label: 'nav.examinations' },
  { id: 'results', label: 'nav.results' },
  { id: 'announcements', label: 'nav.announcements' },
  { id: 'notifications', label: 'nav.notifications' },
  { id: 'documents', label: 'nav.documents' },
  { id: 'help', label: 'nav.help' },
  { id: 'settings', label: 'nav.settings' },
]

export const NAVIGATION_REGISTRY = [
  // Dashboards
  {
    id: 'dashboard-national',
    to: '/dashboard',
    label: 'nav.universityDashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.VIEW_NATIONAL_DASHBOARD,
    group: 'dashboard',
  },
  {
    id: 'dashboard-university',
    to: '/university',
    label: 'nav.universityDashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.VIEW_NATIONAL_DASHBOARD,
    group: 'dashboard',
  },
  {
    id: 'dashboard-school',
    to: '/school',
    label: 'nav.dashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.VIEW_INSTITUTION_DASHBOARD,
    group: 'dashboard',
  },
  {
    id: 'dashboard-college',
    to: '/college',
    label: 'nav.dashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.VIEW_INSTITUTION_DASHBOARD,
    group: 'dashboard',
  },
  {
    id: 'dashboard-institution',
    to: '/institution',
    label: 'nav.dashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.VIEW_INSTITUTION_DASHBOARD,
    group: 'dashboard',
  },
  {
    id: 'dashboard-student',
    to: '/me',
    label: 'nav.dashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
    group: 'dashboard',
  },
  {
    id: 'dashboard-parent',
    to: '/parent',
    label: 'nav.dashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.VIEW_PARENT_PORTAL,
    group: 'dashboard',
  },
  {
    id: 'dashboard-teacher',
    to: '/teacher',
    label: 'nav.dashboard',
    icon: 'dashboard',
    permission: PERMISSIONS.RECORD_ATTENDANCE,
    group: 'dashboard',
  },

  // Academic Setup & Classes
  {
    id: 'institutions-registry',
    to: '/institutions',
    label: 'nav.institutions',
    icon: 'institutions',
    permission: PERMISSIONS.VIEW_COMPLIANCE_MATRIX,
    group: 'academics',
  },
  {
    id: 'academic-setup',
    to: '/academic',
    label: 'nav.academics',
    icon: 'academic',
    permission: PERMISSIONS.MANAGE_ACADEMIC_SETUP,
    group: 'academics',
  },
  {
    id: 'teacher-classes',
    to: '/teacher',
    label: 'nav.classes',
    icon: 'academic',
    permission: PERMISSIONS.RECORD_ATTENDANCE,
    group: 'academics',
  },
  {
    id: 'student-academics',
    to: '/me/academics',
    label: 'nav.academics',
    icon: 'academic',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
    group: 'academics',
  },

  // Student Register & Admissions
  {
    id: 'students-register',
    to: '/students',
    label: 'nav.students',
    icon: 'students',
    permission: PERMISSIONS.VIEW_STUDENT_REGISTER,
    group: 'academics',
  },

  // Attendance & Timetable
  {
    id: 'attendance-record',
    to: '/teacher',
    label: 'nav.attendance',
    icon: 'attendance',
    permission: PERMISSIONS.RECORD_ATTENDANCE,
    group: 'attendance',
  },
  {
    id: 'student-attendance',
    to: '/me/attendance',
    label: 'nav.attendance',
    icon: 'attendance',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
    group: 'attendance',
  },
  {
    id: 'student-timetable',
    to: '/me/timetable',
    label: 'nav.timetable',
    icon: 'timetable',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
    group: 'timetable',
  },

  // Assignments
  {
    id: 'student-assignments',
    to: '/me/assignments',
    label: 'nav.assignments',
    icon: 'assignments',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
    group: 'assignments',
  },

  // Examinations & Results
  {
    id: 'assessments-admin',
    to: '/assessments',
    label: 'nav.examinations',
    icon: 'examinations',
    permission: PERMISSIONS.VIEW_RESULTS,
    group: 'examinations',
  },
  {
    id: 'student-results',
    to: '/me/results',
    label: 'nav.results',
    icon: 'results',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
    group: 'results',
  },

  // Documents & Credentials
  {
    id: 'student-documents',
    to: '/me/id-card',
    label: 'nav.documents',
    icon: 'documents',
    permission: PERMISSIONS.VIEW_OWN_RECORD,
    group: 'documents',
  },
  {
    id: 'upload-csv',
    to: '/upload',
    label: 'nav.upload',
    icon: 'documents',
    permission: PERMISSIONS.IMPORT_CSV,
    group: 'documents',
  },

  // Opportunities & Library
  {
    id: 'library-common',
    to: '/library',
    label: 'nav.library',
    icon: 'library',
    permission: null,
    group: 'academics',
  },
  {
    id: 'opportunities-common',
    to: '/opportunities',
    label: 'nav.opportunities',
    icon: 'opportunities',
    permission: null,
    group: 'academics',
  },

  // Announcements & Notices
  {
    id: 'announcements-view',
    to: '/announcements',
    label: 'nav.announcements',
    icon: 'announcements',
    permission: PERMISSIONS.VIEW_ANNOUNCEMENTS,
    group: 'announcements',
  },

  // Reports
  {
    id: 'reports-export',
    to: '/reports',
    label: 'nav.reports',
    icon: 'reports',
    permission: PERMISSIONS.EXPORT_REPORTS,
    group: 'documents',
  },

  // Notifications Centre
  {
    id: 'notifications-centre',
    to: '/notifications',
    label: 'nav.notifications',
    icon: 'notifications',
    permission: null,
    badgeKey: 'unread_notifications',
    group: 'notifications',
  },

  // Profile & Account Settings
  {
    id: 'profile-settings',
    to: '/profile',
    label: 'nav.profile',
    icon: 'profile',
    permission: null,
    group: 'profile',
  },

  // Help & Support
  {
    id: 'help-support',
    to: '/help',
    label: 'nav.help',
    icon: 'help',
    permission: null,
    group: 'help',
  },
]

export const ROLE_DEFAULT_NAVIGATIONS = {
  student: [
    { to: '/me', label: 'nav.dashboard', icon: 'dashboard', group: 'dashboard' },
    { to: '/me/academics', label: 'nav.academics', icon: 'academic', group: 'academics' },
    { to: '/me/attendance', label: 'nav.attendance', icon: 'attendance', group: 'attendance' },
    { to: '/me/timetable', label: 'nav.timetable', icon: 'timetable', group: 'timetable' },
    { to: '/me/assignments', label: 'nav.assignments', icon: 'assignments', group: 'assignments' },
    { to: '/me/results', label: 'nav.results', icon: 'results', group: 'results' },
    { to: '/me/id-card', label: 'nav.documents', icon: 'documents', group: 'documents' },
    { to: '/announcements', label: 'nav.announcements', icon: 'announcements', group: 'announcements' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications', hasBadge: true, group: 'notifications' },
    { to: '/help', label: 'nav.help', icon: 'help', group: 'help' },
    { to: '/profile', label: 'nav.profile', icon: 'profile', group: 'settings' },
  ],
  parent: [
    { to: '/parent', label: 'nav.dashboard', icon: 'dashboard', group: 'dashboard' },
    { to: '/parent', label: 'nav.children', icon: 'students', group: 'academics' },
    { to: '/parent', label: 'nav.attendance', icon: 'attendance', group: 'attendance' },
    { to: '/parent', label: 'nav.timetable', icon: 'timetable', group: 'timetable' },
    { to: '/assessments', label: 'nav.results', icon: 'results', group: 'results' },
    { to: '/announcements', label: 'nav.announcements', icon: 'announcements', group: 'announcements' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications', hasBadge: true, group: 'notifications' },
    { to: '/help', label: 'nav.help', icon: 'help', group: 'help' },
    { to: '/profile', label: 'nav.profile', icon: 'profile', group: 'settings' },
  ],
  teacher: [
    { to: '/teacher', label: 'nav.dashboard', icon: 'dashboard', group: 'dashboard' },
    { to: '/teacher', label: 'nav.classes', icon: 'academic', group: 'academics' },
    { to: '/teacher', label: 'nav.attendance', icon: 'attendance', group: 'attendance' },
    { to: '/teacher', label: 'nav.timetable', icon: 'timetable', group: 'timetable' },
    { to: '/teacher', label: 'nav.assignments', icon: 'assignments', group: 'assignments' },
    { to: '/assessments', label: 'nav.examinations', icon: 'examinations', group: 'examinations' },
    { to: '/assessments', label: 'nav.results', icon: 'results', group: 'results' },
    { to: '/announcements', label: 'nav.announcements', icon: 'announcements', group: 'announcements' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications', hasBadge: true, group: 'notifications' },
    { to: '/help', label: 'nav.help', icon: 'help', group: 'help' },
    { to: '/profile', label: 'nav.profile', icon: 'profile', group: 'settings' },
  ],
  school_admin: [
    { to: '/school', label: 'nav.dashboard', icon: 'dashboard', group: 'dashboard' },
    { to: '/students', label: 'nav.students', icon: 'students', group: 'academics' },
    { to: '/teacher', label: 'nav.staff', icon: 'staff', group: 'academics' },
    { to: '/academic', label: 'nav.classes', icon: 'academic', group: 'academics' },
    { to: '/teacher', label: 'nav.attendance', icon: 'attendance', group: 'attendance' },
    { to: '/academic', label: 'nav.timetable', icon: 'timetable', group: 'timetable' },
    { to: '/announcements', label: 'nav.announcements', icon: 'announcements', group: 'announcements' },
    { to: '/reports', label: 'nav.reports', icon: 'reports', group: 'documents' },
    { to: '/upload', label: 'nav.documents', icon: 'documents', group: 'documents' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications', hasBadge: true, group: 'notifications' },
    { to: '/help', label: 'nav.help', icon: 'help', group: 'help' },
    { to: '/profile', label: 'nav.settings', icon: 'profile', group: 'settings' },
  ],
  college_admin: [
    { to: '/college', label: 'nav.dashboard', icon: 'dashboard', group: 'dashboard' },
    { to: '/academic', label: 'nav.departments', icon: 'academic', group: 'academics' },
    { to: '/students', label: 'nav.students', icon: 'students', group: 'academics' },
    { to: '/teacher', label: 'nav.staff', icon: 'staff', group: 'academics' },
    { to: '/teacher', label: 'nav.attendance', icon: 'attendance', group: 'attendance' },
    { to: '/assessments', label: 'nav.examinations', icon: 'examinations', group: 'examinations' },
    { to: '/announcements', label: 'nav.announcements', icon: 'announcements', group: 'announcements' },
    { to: '/reports', label: 'nav.reports', icon: 'reports', group: 'documents' },
    { to: '/upload', label: 'nav.documents', icon: 'documents', group: 'documents' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications', hasBadge: true, group: 'notifications' },
    { to: '/help', label: 'nav.help', icon: 'help', group: 'help' },
    { to: '/profile', label: 'nav.settings', icon: 'profile', group: 'settings' },
  ],
  university_admin: [
    { to: '/university', label: 'nav.universityDashboard', icon: 'dashboard', group: 'dashboard' },
    { to: '/institutions', label: 'nav.institutions', icon: 'institutions', group: 'academics' },
    { to: '/academic', label: 'nav.programmes', icon: 'academic', group: 'academics' },
    { to: '/assessments', label: 'nav.examinations', icon: 'examinations', group: 'examinations' },
    { to: '/reports', label: 'nav.reports', icon: 'reports', group: 'documents' },
    { to: '/announcements', label: 'nav.announcements', icon: 'announcements', group: 'announcements' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications', hasBadge: true, group: 'notifications' },
    { to: '/help', label: 'nav.help', icon: 'help', group: 'help' },
    { to: '/profile', label: 'nav.settings', icon: 'profile', group: 'settings' },
  ],
  institution_admin: [
    { to: '/institution', label: 'nav.dashboard', icon: 'dashboard', group: 'dashboard' },
    { to: '/students', label: 'nav.students', icon: 'students', group: 'academics' },
    { to: '/teacher', label: 'nav.staff', icon: 'staff', group: 'academics' },
    { to: '/academic', label: 'nav.academics', icon: 'academic', group: 'academics' },
    { to: '/teacher', label: 'nav.attendance', icon: 'attendance', group: 'attendance' },
    { to: '/assessments', label: 'nav.examinations', icon: 'examinations', group: 'examinations' },
    { to: '/reports', label: 'nav.reports', icon: 'reports', group: 'documents' },
    { to: '/upload', label: 'nav.documents', icon: 'documents', group: 'documents' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications', hasBadge: true, group: 'notifications' },
    { to: '/help', label: 'nav.help', icon: 'help', group: 'help' },
    { to: '/profile', label: 'nav.settings', icon: 'profile', group: 'settings' },
  ],
}
