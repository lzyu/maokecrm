import { useState, useEffect } from 'react'
import { Table, Button, Space, Select, Tag, Modal, Form, message, DatePicker, InputNumber, Input } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useAuthStore } from '../../stores/authStore'
import styles from '../customers/CustomerListPage.module.css'

interface ServiceRecord {
  id: number
  customer_id: number
  customer_name: string | null
  consultant_id: number
  consultant_name: string | null
  service_time: string
  service_content: string
  customer_feedback: string | null
  satisfaction_score: number | null
  created_at: string
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export default function ServiceRecordListPage() {
  const { accessToken } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [records, setRecords] = useState<ServiceRecord[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [customerFilter, setCustomerFilter] = useState<number | undefined>()
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [customers, setCustomers] = useState<Array<{ id: number; name: string }>>([])

  const fetchRecords = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      })
      if (customerFilter) params.append('customer_id', String(customerFilter))

      const response = await fetch(`/api/v1/services/records?${params}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })

      if (!response.ok) throw new Error('Failed to fetch')

      const data: PaginatedResponse<ServiceRecord> = await response.json()
      setRecords(data.items)
      setTotal(data.total)
    } catch (error) {
      message.error('获取服务记录失败')
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
    fetchRecords()
  }, [page, pageSize, customerFilter])

  useEffect(() => {
    fetchCustomers()
  }, [])

  const handleCreate = async (values: any) => {
    try {
      const response = await fetch('/api/v1/services/records', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          ...values,
          service_time: values.service_time?.toISOString(),
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
      fetchRecords()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const columns: ColumnsType<ServiceRecord> = [
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
      render: (text) => text || '-',
    },
    {
      title: '服务时间',
      dataIndex: 'service_time',
      key: 'service_time',
      width: 160,
      render: (text) => (text ? new Date(text).toLocaleString() : '-'),
    },
    {
      title: '服务内容',
      dataIndex: 'service_content',
      key: 'service_content',
      ellipsis: true,
    },
    {
      title: '客户反馈',
      dataIndex: 'customer_feedback',
      key: 'customer_feedback',
      width: 200,
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '满意度',
      dataIndex: 'satisfaction_score',
      key: 'satisfaction_score',
      width: 100,
      render: (score) => (
        <Tag color={score >= 4 ? 'green' : score >= 3 ? 'blue' : 'orange'}>
          {score ? `${score}分` : '-'}
        </Tag>
      ),
    },
    {
      title: '咨询师',
      dataIndex: 'consultant_name',
      key: 'consultant_name',
      width: 100,
      render: (text) => text || '-',
    },
  ]

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>咨询服务</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
          新建服务记录
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
          dataSource={records}
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
        title="新建服务记录"
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
          <Form.Item name="service_time" label="服务时间" rules={[{ required: true, message: '请选择时间' }]}>
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="service_content" label="服务内容" rules={[{ required: true, message: '请输入内容' }]}>
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="customer_feedback" label="客户反馈">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="satisfaction_score" label="满意度评分 (1-5)">
            <InputNumber min={1} max={5} style={{ width: '100%' }} />
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
