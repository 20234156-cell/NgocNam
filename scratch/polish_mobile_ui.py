import re
import sys
import shutil

sys.stdout.reconfigure(encoding='utf-8')

with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("Original length:", len(html))

# 1. Ensure viewport tag is mobile optimized with viewport-fit=cover
if '<meta content="width=device-width, initial-scale=1.0"' in html:
    html = html.replace(
        '<meta content="width=device-width, initial-scale=1.0" name="viewport"/>',
        '<meta content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover" name="viewport"/>'
    )
    print("1. Updated viewport meta tag")

# 2. Add Mobile CSS Enhancements in <style>
mobile_css = """
    /* Mobile-first and iOS touch optimizations */
    @supports (-webkit-touch-callout: none) {
      /* Prevent iOS auto-zoom on form inputs */
      input, select, textarea {
        font-size: 16px !important;
      }
    }
    
    /* Touch-friendly scrolling for horizontal tables */
    .overflow-x-auto {
      -webkit-overflow-scrolling: touch;
    }
    
    /* Safe-area insets for modern edge-to-edge smartphone screens */
    #mobileBottomNav {
      padding-bottom: env(safe-area-inset-bottom, 0px);
      height: calc(4rem + env(safe-area-inset-bottom, 0px));
    }
    
    /* Ensure tap targets are responsive and eliminate tap delay */
    button, a {
      touch-action: manipulation;
    }
"""

if "/* Mobile-first and iOS touch optimizations */" not in html:
    html = html.replace('</style>', mobile_css + '\n  </style>')
    print("2. Injected mobile CSS enhancements")

# 3. Ensure Header title and layout are mobile responsive
# Currently header title:
old_header_title = """          <div class="flex flex-col">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-[17px] text-primary font-bold tracking-tight">HỆ THỐNG THẨM ĐỊNH & PHÊ DUYỆT TÍN DỤNG</span>
              <span class="px-2 py-0.5 rounded bg-surface-container text-secondary font-mono text-[11px] font-bold">DSS v2.4</span>
            </div>
            <span class="text-[12px] text-on-surface-variant">Phân hệ Quyết định Tín dụng Bán lẻ & Khách hàng Cá nhân (XGBoost + TreeSHAP)</span>
          </div>"""

new_header_title = """          <div class="flex flex-col min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-[15px] sm:text-[17px] text-primary font-bold tracking-tight truncate max-w-[200px] sm:max-w-none">VIETCREDIT AI</span>
              <span class="px-2 py-0.5 rounded bg-surface-container text-secondary font-mono text-[10px] sm:text-[11px] font-bold">DSS v2.4</span>
            </div>
            <span class="text-[11px] sm:text-[12px] text-on-surface-variant truncate hidden xs:inline sm:inline">Phân hệ Quyết định Tín dụng Bán lẻ (XGBoost + TreeSHAP)</span>
          </div>"""

if old_header_title in html:
    html = html.replace(old_header_title, new_header_title)
    print("3. Made header title responsive for small screens")

# Also simplify user avatar name on very small screens
old_user_profile = """          <div class="flex items-center gap-3">
            <div class="text-right">
              <div class="text-[14px] text-primary font-bold leading-tight">Nguyễn Văn Minh</div>
              <div class="text-[11px] text-on-surface-variant">Trưởng nhóm Thẩm định Rủi ro</div>
            </div>
            <div class="w-9 h-9 rounded-full bg-primary flex items-center justify-center text-white shadow-sm">
              <span class="material-symbols-outlined text-[20px]">person</span>
            </div>
          </div>"""

new_user_profile = """          <div class="flex items-center gap-2 sm:gap-3">
            <div class="text-right hidden sm:block">
              <div class="text-[14px] text-primary font-bold leading-tight">Nguyễn Văn Minh</div>
              <div class="text-[11px] text-on-surface-variant">Trưởng nhóm Thẩm định Rủi ro</div>
            </div>
            <div class="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-primary flex items-center justify-center text-white shadow-sm shrink-0" title="Nguyễn Văn Minh - Trưởng nhóm Thẩm định">
              <span class="material-symbols-outlined text-[18px] sm:text-[20px]">person</span>
            </div>
          </div>"""

if old_user_profile in html:
    html = html.replace(old_user_profile, new_user_profile)
    print("4. Made user profile header element responsive")

# 4. Ensure sidebar links close sidebar on mobile tap
html = html.replace(
    'onclick="navigateView(\'viewCockpit\', this)"',
    'onclick="navigateView(\'viewCockpit\', this); toggleMobileSidebar(false);"'
)
html = html.replace(
    'onclick="navigateView(\'viewQueue\', this)"',
    'onclick="navigateView(\'viewQueue\', this); toggleMobileSidebar(false);"'
)
html = html.replace(
    'onclick="navigateView(\'viewShap\', this)"',
    'onclick="navigateView(\'viewShap\', this); toggleMobileSidebar(false);"'
)
html = html.replace(
    'onclick="navigateView(\'viewStress\', this)"',
    'onclick="navigateView(\'viewStress\', this); toggleMobileSidebar(false);"'
)
html = html.replace(
    'onclick="navigateView(\'viewCommittee\', this)"',
    'onclick="navigateView(\'viewCommittee\', this); toggleMobileSidebar(false);"'
)
html = html.replace(
    'onclick="navigateView(\'viewAudit\', this)"',
    'onclick="navigateView(\'viewAudit\', this); toggleMobileSidebar(false);"'
)
print("5. Added mobile sidebar close triggers to all mainNav links")

# 5. Replace navigateView implementation with robust mobile-aware controller
old_nav_code = """    // Navigation Router
    function navigateView(viewId, el) {
      document.querySelectorAll('.view-section').forEach(sec => sec.classList.add('hidden'));
      const activeSec = document.getElementById(viewId);
      if (activeSec) activeSec.classList.remove('hidden');

      document.querySelectorAll('#mainNav .nav-link').forEach(link => {
        link.className = "nav-link flex items-center gap-3 px-3 py-2.5 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-all";
      });
      if (el) {
        el.className = "nav-link flex items-center gap-3 px-3 py-2.5 bg-primary-container text-white font-semibold rounded-lg shadow-sm transition-all";
      }

      if (viewId === 'viewQueue') loadQueueFromApi();
      if (viewId === 'viewAudit') loadAuditLogsFromApi();
      if (viewId === 'viewShap') loadFeatureImportanceFromApi();
      if (viewId === 'viewStress') runStressTestSimulation();
    }"""

new_nav_code = """    // ====================================================================
    // MOBILE RESPONSIVE SIDEBAR & BOTTOM NAV CONTROLLERS
    // ====================================================================
    function toggleMobileSidebar(open) {
      const sidebar = document.getElementById('sidebarNav');
      const backdrop = document.getElementById('mobileSidebarBackdrop');
      if (!sidebar || !backdrop) return;
      if (open) {
        sidebar.classList.remove('-translate-x-full');
        backdrop.classList.remove('hidden');
        document.body.classList.add('overflow-hidden', 'lg:overflow-auto');
      } else {
        sidebar.classList.add('-translate-x-full');
        backdrop.classList.add('hidden');
        document.body.classList.remove('overflow-hidden', 'lg:overflow-auto');
      }
    }

    function setActiveMobileTab(viewId) {
      document.querySelectorAll('#mobileBottomNav .mobile-tab-btn').forEach(btn => {
        const isTarget = btn.getAttribute('data-target') === viewId;
        if (isTarget) {
          btn.classList.add('text-primary');
          btn.classList.remove('text-on-surface-variant');
        } else {
          btn.classList.remove('text-primary');
          btn.classList.add('text-on-surface-variant');
        }
      });
    }

    // Navigation Router (Desktop Sidebar + Mobile Bottom Nav Unified)
    function navigateView(viewId, el) {
      document.querySelectorAll('.view-section').forEach(sec => sec.classList.add('hidden'));
      const activeSec = document.getElementById(viewId);
      if (activeSec) activeSec.classList.remove('hidden');

      // Reset desktop sidebar links
      document.querySelectorAll('#mainNav .nav-link').forEach(link => {
        link.className = "nav-link flex items-center gap-3 px-3 py-2.5 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-all";
      });

      // Highlight target sidebar link
      if (el && el.classList && el.classList.contains('nav-link')) {
        el.className = "nav-link flex items-center gap-3 px-3 py-2.5 bg-primary-container text-white font-semibold rounded-lg shadow-sm transition-all";
      } else {
        const matchingLink = document.querySelector(`#mainNav .nav-link[data-target="${viewId}"]`);
        if (matchingLink) {
          matchingLink.className = "nav-link flex items-center gap-3 px-3 py-2.5 bg-primary-container text-white font-semibold rounded-lg shadow-sm transition-all";
        }
      }

      // Highlight mobile bottom tab
      setActiveMobileTab(viewId);

      // Close mobile drawer if open
      toggleMobileSidebar(false);

      // Smooth scroll back to top of workspace
      window.scrollTo({ top: 0, behavior: 'smooth' });

      // Trigger respective data loaders
      if (viewId === 'viewQueue') loadQueueFromApi();
      if (viewId === 'viewAudit') loadAuditLogsFromApi();
      if (viewId === 'viewShap') loadFeatureImportanceFromApi();
      if (viewId === 'viewStress') runStressTestSimulation();
    }"""

if old_nav_code in html:
    html = html.replace(old_nav_code, new_nav_code)
    print("6. Successfully replaced navigateView and added toggleMobileSidebar & setActiveMobileTab")
else:
    print("WARNING: old_nav_code not matched exactly!")

# 6. Ensure modals are mobile friendly
# Check decisionModal paper sizing
html = html.replace(
    'id="decisionPaper" class="bg-white w-full max-w-4xl shadow-2xl rounded-2xl border border-slate-200 overflow-hidden relative"',
    'id="decisionPaper" class="bg-white w-full max-w-4xl shadow-2xl rounded-2xl border border-slate-200 overflow-hidden relative mx-2 sm:mx-auto"'
)
html = html.replace(
    'id="auditModalPaper" class="bg-white w-full max-w-4xl shadow-2xl rounded-2xl border border-slate-200 overflow-hidden relative"',
    'id="auditModalPaper" class="bg-white w-full max-w-4xl shadow-2xl rounded-2xl border border-slate-200 overflow-hidden relative mx-2 sm:mx-auto"'
)

# 7. Ensure mobile bottom nav has all 5 tabs and safe area
# Let's verify #mobileBottomNav
if 'id="mobileBottomNav"' in html:
    print("7. mobileBottomNav is confirmed present in HTML")

with open('app/cockpit.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated app/cockpit.html successfully.")

# Sync to app/index.html
shutil.copyfile('app/cockpit.html', 'app/index.html')
print("Synchronized app/cockpit.html -> app/index.html successfully!")
