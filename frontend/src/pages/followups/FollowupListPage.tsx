import { useState, useEffect } from 'react'
import { Table, Button, Space, Input, Select, Tag, Modal, Form, message, DatePicker } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useAuthStore } from '../../stores/authStore'
import styles from '../customers/CustomerListPage.module.css'

interface Followup {
  id: number
  customer_id: number
  customer_name: string | null
  sales_id: number
  sales_name: string | null
  followup_time: string
  contact_method: string
  content: string
  result: string | null
  next_action_time: string | null
  created_at: string
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

const contactMethodLabels: Record<string, string> = {
  phone: '电话',
  wechat: '微信',
  visit: '上门',
  email: '邮件',
  other: '其他',
}

const resultLabels: Record<string, string> = {
  no_answer: '未接通',
  contacted: '已联系',
  interested: '有意向',
  rejected: '已拒绝',
  pending: '待跟进',
}

export default function FollowupListPage() {
  const { accessToken, user } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [followups, setFollowups] = useState<Followup[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [customerFilter, setCustomerFilter] = useState<number | undefined>()
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [customers, setCustomers] = useState<Array<{ id: number; name: string }>>([])

  const fetchFollowups = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      })
      if (customerFilter) params.append('customer_id', String(customerFilter))

      const response = await fetch(`/api/v1/followups?${params}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })

      if (!response.ok) throw new Error('Failed to fetch')

      const data: PaginatedResponse<Followup> = await response.json()
      setFollowups(data.items)
      setTotal(data.total)
    } catch (error) {
      message.error('获取跟进记录失败')
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

  useEffect(() => {
    fetchFollowups()
  }, [page, pageSize, customerFilter])

  useEffect(() => {
    fetchCustomers()
  }, [])

  const handleCreate = async (values: any) => {
    try {
      const response = await fetch('/api/v1/followups', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          ...values,
          followup_time: values.followup_time?.toISOString(),
          next_action_time: values.next_action_time?.toISOString(),
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
      fetchFollowups()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const columns: ColumnsType<Followup> = [
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
      render: (text) => text || '-',
    },
    {
      title: '跟进时间',
      dataIndex: 'followup_time',
      key: 'followup_time',
      width: 160,
      render: (text) => (text ? new Date(text).toLocaleString() : '-'),
    },
    {
      title: '联系方式',
      dataIndex: 'contact_method',
      key: 'contact_method',
      width: 100,
      render: (text) => contactMethodLabels[text] || text,
    },
    {
      title: '跟进内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
    {
      title: '结果',
      dataIndex: 'result',
      key: 'result',
      width: 100,
      render: (text) => (
        <Tag color={text === 'interested' ? 'green' : text === 'rejected' ? 'red' : 'default'}>
          {resultLabels[text] || text || '-'}
        </Tag>
      ),
    },
    {
      title: '下次跟进',
      dataIndex: 'next_action_time',
      key: 'next_action_time',
      width: 160,
      render: (text) => (text ? new Date(text).toLocaleString() : '-'),
    },
    {
      title: '销售',
      dataIndex: 'sales_name',
      key: 'sales_name',
      width: 100,
      render: (text) => text || '-',
    },
  ]

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>跟进记录</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
          新建跟进
        </Button>
      </div>

      <div className={styles.filters}>
        <Space>
          <Select
            placeholder="筛选客户"
            value={customerFilter}
            onChange={setCustomerFilter}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 200 }}
            options={customers.map(c => ({ value: c.id, label: c.name }))}
          />
        </Space>
      </div>

      <div className={styles.tableContainer}>
        <Table
          columns={columns}
          dataSource={followups}
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
        title="新建跟进记录"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="customer_id" label="客户" rules={[{ required: true, message: '请选择客户' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={customers.map(c => ({ value: c.id, label: c.name }))}
            />
          </Form.Item>
          <Form.Item name="followup_time" label="跟进时间" rules={[{ required: true, message: '请选择时间' }]}>
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="contact_method" label="联系方式" rules={[{ required: true, message: '请选择联系方式' }]}>
            <Select options={Object.entries(contactMethodLabels).map(([value, label]) => ({ value, label }))} />
          </Form.Item>
          <Form.Item name="content" label="跟进内容" rules={[{ required: true, message: '请输入内容' }]}>
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="result" label="跟进结果">
            <Select allowClear options={Object.entries(resultLabels).map(([value, label]) => ({ value, label }))} />
          </Form.Item>
          <Form.Item name="next_action_time" label="下次跟进时间">
            <DatePicker showTime style={{ width: '100%' }} />
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
