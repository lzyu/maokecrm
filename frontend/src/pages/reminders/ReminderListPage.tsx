import { useState, useEffect } from 'react'
import { Table, Button, Space, Select, Tag, Modal, Form, message, DatePicker, Input } from 'antd'
import { PlusOutlined, CheckOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useAuthStore } from '../../stores/authStore'
import styles from '../customers/CustomerListPage.module.css'

interface Reminder {
  id: number
  customer_id: number
  customer_name: string | null
  assignee_user_id: number
  assignee_name: string | null
  reminder_type: string
  reminder_time: string
  priority: string
  status: string
  content: string | null
  created_at: string
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

const reminderTypeLabels: Record<string, string> = {
  followup: '跟进提醒',
  renewal: '续费提醒',
  progress_check: '进度检查',
  other: '其他',
}

const priorityLabels: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
}

const priorityColors: Record<string, string> = {
  low: 'default',
  medium: 'blue',
  high: 'red',
}

const statusLabels: Record<string, string> = {
  pending: '待处理',
  done: '已完成',
  canceled: '已取消',
}

const statusColors: Record<string, string> = {
  pending: 'orange',
  done: 'green',
  canceled: 'default',
}

export default function ReminderListPage() {
  const { accessToken, user } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [reminders, setReminders] = useState<Reminder[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [priorityFilter, setPriorityFilter] = useState<string | undefined>()
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [customers, setCustomers] = useState<Array<{ id: number; name: string }>>([])
  const [users, setUsers] = useState<Array<{ id: number; name: string }>>([])

  const isAdmin = user?.role_name === 'admin' || user?.role_name === 'super_admin'

  const fetchReminders = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      })
      if (statusFilter) params.append('status', statusFilter)
      if (priorityFilter) params.append('priority', priorityFilter)

      const response = await fetch(`/api/v1/reminders?${params}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })

      if (!response.ok) throw new Error('Failed to fetch')

      const data: PaginatedResponse<Reminder> = await response.json()
      setReminders(data.items)
      setTotal(data.total)
    } catch (error) {
      message.error('获取提醒失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchCustomers = async () => {
    try {
      const response = await fetch('/api/v1/customers?page=1&page_size=100', {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      if (response.ok) {
        const data = await response.json()
        setCustomers(data.items.map((c: any) => ({ id: c.id, name: c.name })))
      }
    } catch (error) {
      console.error('Failed to fetch customers:', error)
    }
  }

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/v1/users?page=1&page_size=100', {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      if (response.ok) {
        const data = await response.json()
        setUsers(data.items.map((u: any) => ({ id: u.id, name: u.real_name || u.name })))
      }
    } catch (error) {
      console.error('Failed to fetch users:', error)
    }
  }

  useEffect(() => {
    fetchReminders()
  }, [page, pageSize, statusFilter, priorityFilter])

  useEffect(() => {
    fetchCustomers()
    fetchUsers()
  }, [])

  const handleCreate = async (values: any) => {
    try {
      const response = await fetch('/api/v1/reminders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          ...values,
          reminder_time: values.reminder_time?.toISOString(),
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        message.error(error.detail || '创建失败')
        return
      }

      message.success('创建成功')
      setCreateModalOpen(false)
      form.resetFields()
      fetchReminders()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleMarkDone = async (id: number) => {
    try {
      const response = await fetch(`/api/v1/reminders/${id}/done`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${accessToken}` },
      })

      if (!response.ok) {
        const error = await response.json()
        message.error(error.detail || '操作失败')
        return
      }

      message.success('已标记为完成')
      fetchReminders()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const columns: ColumnsType<Reminder> = [
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
      render: (text) => text || '-',
    },
    {
      title: '提醒类型',
      dataIndex: 'reminder_type',
      key: 'reminder_type',
      width: 100,
      render: (text) => reminderTypeLabels[text] || text,
    },
    {
      title: '提醒时间',
      dataIndex: 'reminder_time',
      key: 'reminder_time',
      width: 160,
      render: (text) => (text ? new Date(text).toLocaleString() : '-'),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (text) => (
        <Tag color={priorityColors[text] || 'default'}>{priorityLabels[text] || text}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (text) => (
        <Tag color={statusColors[text] || 'default'}>{statusLabels[text] || text}</Tag>
      ),
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '负责人',
      dataIndex: 'assignee_name',
      key: 'assignee_name',
      width: 100,
      render: (text) => text || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        record.status === 'pending' && (
          <Button
            type="link"
            icon={<CheckOutlined />}
            onClick={() => handleMarkDone(record.id)}
          >
            完成
          </Button>
        )
      ),
    },
  ]

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>服务提醒</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
          新建提醒
        </Button>
      </div>

      <div className={styles.filters}>
        <Space>
          <Select
            placeholder="状态"
            value={statusFilter}
            onChange={setStatusFilter}
            allowClear
            style={{ width: 120 }}
            options={Object.entries(statusLabels).map(([value, label]) => ({ value, label }))}
          />
          <Select
            placeholder="优先级"
            value={priorityFilter}
            onChange={setPriorityFilter}
            allowClear
            style={{ width: 120 }}
            options={Object.entries(priorityLabels).map(([value, label]) => ({ value, label }))}
          />
        </Space>
      </div>

      <div className={styles.tableContainer}>
        <Table
          columns={columns}
          dataSource={reminders}
          rowKey="id"
          loading={loading}
          scroll={{ x: 'max-content' }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (p, ps) => { setPage(p); setPageSize(ps); },
          }}
        />
      </div>

      <Modal
        title="新建服务提醒"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate} initialValues={{ priority: 'medium' }}>
          <Form.Item name="customer_id" label="客户" rules={[{ required: true, message: '请选择客户' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={customers.map(c => ({ value: c.id, label: c.name }))}
            />
          </Form.Item>
          <Form.Item name="assignee_user_id" label="负责人" rules={[{ required: true, message: '请选择负责人' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={users.map(u => ({ value: u.id, label: u.name }))}
            />
          </Form.Item>
          <Form.Item name="reminder_type" label="提醒类型" rules={[{ required: true, message: '请选择类型' }]}>
            <Select options={Object.entries(reminderTypeLabels).map(([value, label]) => ({ value, label }))} />
          </Form.Item>
          <Form.Item name="reminder_time" label="提醒时间" rules={[{ required: true, message: '请选择时间' }]}>
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="priority" label="优先级">
            <Select options={Object.entries(priorityLabels).map(([value, label]) => ({ value, label }))} />
          </Form.Item>
          <Form.Item name="content" label="提醒内容">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">创建</Button>
              <Button onClick={() => setCreateModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
