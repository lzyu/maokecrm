export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ADMIN: 'admin',
  SALES: 'sales',
  CONSULTANT: 'consultant',
} as const

export const ROLE_LABELS: Record<string, string> = {
  super_admin: '超级管理员',
  admin: '管理员',
  sales: '销售',
  consultant: '咨询师',
}

export const CUSTOMER_STATUS = {
  POTENTIAL: 'potential',
  NEW: 'new',
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  LOST: 'lost',
} as const

export const CUSTOMER_STATUS_LABELS: Record<string, string> = {
  potential: '潜在客户',
  new: '新客户',
  active: '活跃客户',
  inactive: '不活跃',
  lost: '已流失',
}

export const CUSTOMER_STATUS_COLORS: Record<string, string> = {
  potential: 'default',
  new: 'blue',
  active: 'green',
  inactive: 'orange',
  lost: 'red',
}
