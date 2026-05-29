import * as React from 'react'

function Label(props: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70" {...props} />
}

export { Label }
