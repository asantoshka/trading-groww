import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'

import Sidebar from './Sidebar'
import TopBar from './TopBar'

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    setSidebarOpen(false)
  }, [location.pathname])

  return (
    <div className="h-screen overflow-hidden bg-bg">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="ml-0 flex h-screen min-w-0 flex-col md:ml-[220px]">
        <TopBar onMenuClick={() => setSidebarOpen((prev) => !prev)} />
        <main className="mt-[56px] min-w-0 flex-1 overflow-y-auto px-4 py-4 sm:px-5 sm:py-5 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
