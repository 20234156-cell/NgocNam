import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update <aside> to have id="sidebarNav" and responsive classes
old_aside = '<aside class="fixed left-0 top-0 h-full w-72 bg-surface-container-lowest shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-50 flex flex-col justify-between border-r border-surface-container">'
new_aside = '''<!-- Mobile Backdrop Overlay -->
  <div id="mobileSidebarBackdrop" class="fixed inset-0 bg-primary/60 backdrop-blur-xs z-40 hidden lg:hidden transition-opacity" onclick="toggleMobileSidebar(false)"></div>

  <!-- SIDEBAR NAVIGATION (Responsive Drawer) -->
  <aside id="sidebarNav" class="fixed left-0 top-0 h-full w-72 bg-surface-container-lowest shadow-2xl lg:shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-50 flex flex-col justify-between border-r border-surface-container -translate-x-full lg:translate-x-0 transition-transform duration-300 ease-in-out">'''

if old_aside in html:
    html = html.replace(old_aside, new_aside)
    print("1. Replaced <aside> with responsive drawer")
else:
    print("old_aside not found!")

# Add close button inside Logo Header of sidebar on mobile
old_logo_header = '''      <!-- Logo Header -->
      <div class="h-20 px-6 flex items-center gap-3 bg-primary">
        <div class="w-9 h-9 rounded-lg bg-surface-container-lowest flex items-center justify-center">
          <span class="material-symbols-outlined text-primary text-[24px]">account_balance</span>
        </div>
        <div class="flex flex-col">
          <span class="text-[17px] font-bold text-white tracking-tight">VIETCREDIT AI</span>
          <span class="text-[11px] text-surface-variant font-medium tracking-wider">RISK DSS COCKPIT</span>
        </div>
      </div>'''

new_logo_header = '''      <!-- Logo Header -->
      <div class="h-20 px-6 flex items-center justify-between bg-primary">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-lg bg-surface-container-lowest flex items-center justify-center">
            <span class="material-symbols-outlined text-primary text-[24px]">account_balance</span>
          </div>
          <div class="flex flex-col">
            <span class="text-[17px] font-bold text-white tracking-tight">VIETCREDIT AI</span>
            <span class="text-[11px] text-surface-variant font-medium tracking-wider">RISK DSS COCKPIT</span>
          </div>
        </div>
        <button type="button" class="lg:hidden w-8 h-8 rounded-lg bg-white/10 text-white flex items-center justify-center hover:bg-white/20 transition-colors" onclick="toggleMobileSidebar(false)">
          <span class="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>'''

if old_logo_header in html:
    html = html.replace(old_logo_header, new_logo_header)
    print("2. Added mobile close button to sidebar logo header")
else:
    print("old_logo_header not found!")

# 2. Update Top Header Wrapper (<div class="pl-72">) and <header>
old_header_wrap = '''  <!-- TOP HEADER -->
  <div class="pl-72">
    <header class="fixed top-0 left-72 right-0 h-20 bg-surface-container-lowest/95 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-40 border-b border-surface-container">
      <div class="w-full h-20 px-8 flex items-center justify-between gap-6">
        <div class="flex items-center gap-4 min-w-0">'''

new_header_wrap = '''  <!-- TOP HEADER -->
  <div class="pl-0 lg:pl-72 w-full transition-all">
    <header class="fixed top-0 left-0 lg:left-72 right-0 h-16 sm:h-20 bg-surface-container-lowest/95 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-30 border-b border-surface-container">
      <div class="w-full h-16 sm:h-20 px-4 sm:px-8 flex items-center justify-between gap-3 sm:gap-6">
        <div class="flex items-center gap-2.5 sm:gap-4 min-w-0">
          <!-- Mobile Hamburger Toggle -->
          <button type="button" class="lg:hidden p-2 rounded-xl bg-surface-container hover:bg-surface-container-high text-primary flex items-center justify-center transition-colors shrink-0" onclick="toggleMobileSidebar(true)" title="Mở menu quản trị">
            <span class="material-symbols-outlined text-[22px]">menu</span>
          </button>'''

if old_header_wrap in html:
    html = html.replace(old_header_wrap, new_header_wrap)
    print("3. Replaced top header wrapper with responsive header")
else:
    print("old_header_wrap not found!")

# 3. Update <main> padding for mobile bottom bar
old_main = '<main class="w-full pt-24 px-8 pb-16 min-h-screen">'
new_main = '<main class="w-full pt-20 sm:pt-24 px-3 sm:px-8 pb-28 lg:pb-16 min-h-screen">'

if old_main in html:
    html = html.replace(old_main, new_main)
    print("4. Updated <main> padding for mobile")
else:
    print("old_main not found!")

# 4. Add Mobile Bottom Navigation Bar before </body>
mobile_bottom_nav_html = '''
  <!-- ==================================================================== -->
  <!-- MOBILE BOTTOM NAVIGATION BAR (FIXED FOR SMARTPHONES) -->
  <!-- ==================================================================== -->
  <nav id="mobileBottomNav" class="fixed bottom-0 left-0 right-0 h-16 bg-white/95 backdrop-blur-md border-t border-surface-container flex items-center justify-around z-40 lg:hidden px-1 shadow-[0_-4px_16px_rgba(0,0,0,0.06)] font-mono">
    <button onclick="navigateView('viewCockpit', this); setActiveMobileTab('viewCockpit')" class="mobile-tab-btn flex flex-col items-center justify-center flex-1 py-1 text-primary" data-target="viewCockpit">
      <span class="material-symbols-outlined text-[22px]">analytics</span>
      <span class="text-[10px] font-bold mt-0.5">Thẩm định</span>
    </button>
    <button onclick="navigateView('viewQueue', this); setActiveMobileTab('viewQueue')" class="mobile-tab-btn relative flex flex-col items-center justify-center flex-1 py-1 text-on-surface-variant hover:text-primary" data-target="viewQueue">
      <span class="material-symbols-outlined text-[22px]">inbox</span>
      <span class="text-[10px] font-bold mt-0.5">Hàng đợi</span>
      <span class="absolute top-1 right-2 sm:right-4 px-1.5 py-0.2 rounded-full bg-secondary text-white text-[9px] font-bold" id="badgeQueueCountMobile">14</span>
    </button>
    <button onclick="navigateView('viewStress', this); setActiveMobileTab('viewStress')" class="mobile-tab-btn flex flex-col items-center justify-center flex-1 py-1 text-on-surface-variant hover:text-primary" data-target="viewStress">
      <span class="material-symbols-outlined text-[22px]">crisis_alert</span>
      <span class="text-[10px] font-bold mt-0.5">Stress-test</span>
    </button>
    <button onclick="navigateView('viewCommittee', this); setActiveMobileTab('viewCommittee')" class="mobile-tab-btn flex flex-col items-center justify-center flex-1 py-1 text-on-surface-variant hover:text-primary" data-target="viewCommittee">
      <span class="material-symbols-outlined text-[22px]">gavel</span>
      <span class="text-[10px] font-bold mt-0.5">Hội đồng</span>
    </button>
    <button onclick="navigateView('viewAudit', this); setActiveMobileTab('viewAudit')" class="mobile-tab-btn flex flex-col items-center justify-center flex-1 py-1 text-on-surface-variant hover:text-primary" data-target="viewAudit">
      <span class="material-symbols-outlined text-[22px]">history_edu</span>
      <span class="text-[10px] font-bold mt-0.5">Kiểm toán</span>
    </button>
  </nav>
'''

if 'id="mobileBottomNav"' not in html:
    idx_close_body = html.rfind('</body>')
    if idx_close_body != -1:
        html = html[:idx_close_body] + mobile_bottom_nav_html + "\n" + html[idx_close_body:]
        print("5. Added Mobile Bottom Navigation Bar")
    else:
        print("</body> not found!")

# 5. Update floating batch bars position for mobile
html = html.replace('id="queueBatchBar" class="hidden fixed bottom-6', 'id="queueBatchBar" class="hidden fixed bottom-20 lg:bottom-6')
html = html.replace('id="auditBatchBar" class="hidden fixed bottom-6', 'id="auditBatchBar" class="hidden fixed bottom-20 lg:bottom-6')
print("6. Updated batch bars position for mobile")

# 6. Add Mobile JS functions
mobile_js = '''
    // ====================================================================
    // MOBILE RESPONSIVE NAVIGATION HELPERS
    // ====================================================================
    function toggleMobileSidebar(open) {
      const sidebar = document.getElementById('sidebarNav');
      const backdrop = document.getElementById('mobileSidebarBackdrop');
      if (!sidebar || !backdrop) return;
      if (open) {
        sidebar.classList.remove('-translate-x-full');
        backdrop.classList.remove('hidden');
      } else {
        sidebar.classList.add('-translate-x-full');
        backdrop.classList.add('hidden');
      }
    }

    function setActiveMobileTab(viewId) {
      document.querySelectorAll('.mobile-tab-btn').forEach(btn => {
        if (btn.dataset.target === viewId) {
          btn.classList.add('text-primary');
          btn.classList.remove('text-on-surface-variant');
        } else {
          btn.classList.remove('text-primary');
          btn.classList.add('text-on-surface-variant');
        }
      });
      toggleMobileSidebar(false);
    }
'''

# Update navigateView to automatically call setActiveMobileTab and close sidebar
old_nav_view = """    function navigateView(viewId, element) {
      document.querySelectorAll('.view-section').forEach(sec => {
        sec.classList.add('hidden');
      });

      const target = document.getElementById(viewId);
      if (target) {
        target.classList.remove('hidden');
      }

      document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('bg-primary-container', 'text-white', 'shadow-sm');
        link.classList.add('text-on-surface-variant');
      });

      if (element) {
        element.classList.add('bg-primary-container', 'text-white', 'shadow-sm');
        element.classList.remove('text-on-surface-variant');
      }"""

new_nav_view = """    function navigateView(viewId, element) {
      document.querySelectorAll('.view-section').forEach(sec => {
        sec.classList.add('hidden');
      });

      const target = document.getElementById(viewId);
      if (target) {
        target.classList.remove('hidden');
      }

      document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('bg-primary-container', 'text-white', 'shadow-sm');
        link.classList.add('text-on-surface-variant');
      });

      if (element && element.classList.contains('nav-link')) {
        element.classList.add('bg-primary-container', 'text-white', 'shadow-sm');
        element.classList.remove('text-on-surface-variant');
      } else {
        const matchingLink = document.querySelector(`.nav-link[data-target="${viewId}"]`);
        if (matchingLink) {
          matchingLink.classList.add('bg-primary-container', 'text-white', 'shadow-sm');
          matchingLink.classList.remove('text-on-surface-variant');
        }
      }

      setActiveMobileTab(viewId);
      window.scrollTo({ top: 0, behavior: 'smooth' });"""

if old_nav_view in html:
    html = html.replace(old_nav_view, mobile_js + "\n" + new_nav_view)
    print("7. Updated navigateView with mobile sync")
else:
    print("old_nav_view not found!")

# Also sync queue count badge on mobile
html = html.replace("document.getElementById('badgeQueueCount').textContent = queueData.length;", "document.getElementById('badgeQueueCount').textContent = queueData.length;\n      const mBadge = document.getElementById('badgeQueueCountMobile'); if (mBadge) mBadge.textContent = queueData.length;")

with open('app/cockpit.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Successfully upgraded app/cockpit.html with Mobile-First Responsive UI!")
