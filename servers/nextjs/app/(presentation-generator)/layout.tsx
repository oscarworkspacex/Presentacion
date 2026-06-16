import React from 'react'
import { ConfigurationInitializer } from '../ConfigurationInitializer'
import { LayoutProvider } from './context/LayoutContext'

const layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div>
      <ConfigurationInitializer>
        <LayoutProvider>
          {children}
        </LayoutProvider>
      </ConfigurationInitializer>
    </div>
  )
}

export default layout
