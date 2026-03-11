import { createApp } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js';
import { apiRequest } from './api.js';
import { LoginRegisterPanel } from './components/LoginRegisterPanel.js';
import { AdminDashboard } from './components/AdminDashboard.js';
import { CompanyDashboard } from './components/CompanyDashboard.js';
import { StudentDashboard } from './components/StudentDashboard.js';

createApp({
  components: { LoginRegisterPanel, AdminDashboard, CompanyDashboard, StudentDashboard },
  data() {
    return {
      token: localStorage.getItem('token') || '',
      user: JSON.parse(localStorage.getItem('user') || 'null'),
      message: '',
      state: {
        login: { email: 'admin@ppa.local', password: 'admin123' },
        student: { email: '', password: '', full_name: '', branch: '', cgpa: '', year: '' },
        company: { email: '', password: '', company_name: '', hr_contact: '', website: '' },
        stats: {},
        adminData: {},
        searchQ: '',
        companyData: {},
        drive: { job_title: '', job_description: '', eligible_branch: '', eligible_year: '', min_cgpa: '', application_deadline: '' },
        studentData: {},
        drives: [],
        applications: [],
      },
    };
  },
  methods: {
    async initDb() { return this.run(async () => this.message = (await apiRequest('/init', { method: 'POST' })).message); },
    async login() {
      return this.run(async () => {
        const data = await apiRequest('/auth/login', { method: 'POST', body: this.state.login });
        this.token = data.access_token; this.user = data.user;
        localStorage.setItem('token', this.token); localStorage.setItem('user', JSON.stringify(this.user));
        this.message = 'Login successful';
      });
    },
    async registerStudent() { return this.run(async () => this.message = (await apiRequest('/auth/register/student', { method: 'POST', body: this.state.student })).message); },
    async registerCompany() { return this.run(async () => this.message = (await apiRequest('/auth/register/company', { method: 'POST', body: this.state.company })).message); },
    async loadAdminStats() { return this.run(async () => this.state.stats = await apiRequest('/admin/dashboard', { token: this.token })); },
    async loadCompanies() { return this.run(async () => this.state.adminData = await apiRequest('/admin/companies', { token: this.token })); },
    async loadStudents() { return this.run(async () => this.state.adminData = await apiRequest('/admin/students', { token: this.token })); },
    async searchAdmin() { return this.run(async () => this.state.adminData = await apiRequest(`/admin/search?q=${encodeURIComponent(this.state.searchQ)}`, { token: this.token })); },
    async companyDashboard() { return this.run(async () => this.state.companyData = await apiRequest('/company/dashboard', { token: this.token })); },
    async companyDrives() { return this.run(async () => this.state.companyData = await apiRequest('/company/drives', { token: this.token })); },
    async companyApplications() { return this.run(async () => this.state.companyData = await apiRequest('/company/applications', { token: this.token })); },
    async createDrive() { return this.run(async () => this.message = (await apiRequest('/company/drives', { token: this.token, method: 'POST', body: this.state.drive })).message); },
    async studentDashboard() { return this.run(async () => this.state.studentData = await apiRequest('/student/dashboard', { token: this.token })); },
    async studentDrives() { return this.run(async () => this.state.drives = await apiRequest('/student/drives', { token: this.token })); },
    async studentApplications() { return this.run(async () => this.state.applications = await apiRequest('/student/applications', { token: this.token })); },
    async applyDrive(id) { return this.run(async () => this.message = (await apiRequest(`/student/drives/${id}/apply`, { token: this.token, method: 'POST' })).message); },
    async exportCsv() {
      return this.run(async () => {
        const requestTask = await apiRequest('/student/export/request', { token: this.token, method: 'POST' });
        let taskData = requestTask;
        if (!taskData.download_ready) {
          this.message = 'Preparing CSV export in background...';
          for (let i = 0; i < 8; i += 1) {
            await new Promise((resolve) => setTimeout(resolve, 1200));
            taskData = await apiRequest(`/student/export/status/${requestTask.task_id}`, { token: this.token });
            if (taskData.download_ready) break;
          }
        }

        const downloadUrl = taskData.download_ready
          ? `http://localhost:5000/api/student/export/download/${requestTask.task_id}`
          : 'http://localhost:5000/api/student/export';

        const response = await fetch(downloadUrl, { headers: { Authorization: `Bearer ${this.token}` } });
        if (!response.ok) throw new Error('Export not ready yet');
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = 'application_history.csv'; a.click();
        URL.revokeObjectURL(url);
        this.message = 'CSV export is ready and downloaded';
      });
    },
    run(fn) { return fn().catch((e) => this.message = e.message || 'Operation failed'); },
    logout() { this.token=''; this.user=null; localStorage.clear(); },
  },
  template: `
    <div>
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="mb-0">PPA - V2</h4>
        <div>
          <span v-if="user" class="badge text-bg-primary me-2">{{ user.role }}</span>
          <button v-if="user" class="btn btn-outline-danger btn-sm" @click="logout">Logout</button>
        </div>
      </div>

      <login-register-panel
        v-if="!token"
        :state="state"
        :on-login="login"
        :on-register-student="registerStudent"
        :on-register-company="registerCompany"
        :on-init-db="initDb"
      />

      <admin-dashboard
        v-else-if="user && user.role==='admin'"
        :state="state"
        :reload-stats="loadAdminStats"
        :load-companies="loadCompanies"
        :load-students="loadStudents"
        :search="searchAdmin"
      />

      <company-dashboard
        v-else-if="user && user.role==='company'"
        :state="state"
        :load-dashboard="companyDashboard"
        :load-drives="companyDrives"
        :load-applications="companyApplications"
        :create-drive="createDrive"
      />

      <student-dashboard
        v-else-if="user && user.role==='student'"
        :state="state"
        :load-student-dashboard="studentDashboard"
        :load-eligible-drives="studentDrives"
        :load-applications="studentApplications"
        :apply-drive="applyDrive"
        :export-csv="exportCsv"
      />

      <div v-if="message" class="alert alert-info mt-3">{{ message }}</div>
    </div>
  `,
}).mount('#app');
