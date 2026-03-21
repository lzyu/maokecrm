import { useState, useEffect } from 'react'
import { Table, Button, Space, Select, Tag, Upload, message, Modal, TableColumnsType } from 'antd'
import { UploadOutlined, EyeOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../stores/authStore'
import styles from '../customers/CustomerListPage.module.css'

interface ImportBatch {
  id: number
  batch_no: string
  import_type: string
  file_name: string
  status: string
  total_rows: number
  success_rows: number
  failed_rows: number
  started_at: string
  finished_at: string | null
  created_at: string
}

interface ImportError {
  id: number
  row_no: number
  error_code: string
  error_message: string
  row_data: any
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

const importTypeLabels: Record<string, string> = {
  course_purchase: '课程购买记录',
  course_attendance: '上课记录',
}

const statusLabels: Record<string, string> = {
  processing: '处理中',
  completed: '已完成',
  failed: '失败',
  partial_success: '部分成功',
}

const statusColors: Record<string, string> = {
  processing: 'blue',
  completed: 'green',
  failed: 'red',
  partial_success: 'orange',
}

export default function ImportPage() {
  const { accessToken, user } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [batches, setBatches] = useState<ImportBatch[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [importTypeFilter, setImportTypeFilter] = useState<string | undefined>()
  const [errorModalOpen, setErrorModalOpen] = useState(false)
  const [errors, setErrors] = useState<ImportError[]>([])
  const [selectedBatch, setSelectedBatch] = useState<ImportBatch | null>(null)

  const isAdmin = user?.role_name === 'admin' || user?.role_name === 'super_admin'

  const fetchBatches = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      })
      if (importTypeFilter) params.append('import_type', importTypeFilter)

      const response = await fetch(`/api/v1/imports/batches?${params}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })

      if (!response.ok) throw new Error('Failed to fetch')

      const data: PaginatedResponse<ImportBatch> = await response.json()
      setBatches(data.items)
      setTotal(data.total)
    } catch (error) {
      message.error('获取导入记录失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAdmin) {
      fetchBatches()
    }
  }, [page, pageSize, importTypeFilter, isAdmin])

  const handleUpload = async (file: File, importType: 'course_purchase' | 'course_attendance') => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const endpoint = importType === 'course_purchase' ? '/api/v1/imports/course-purchases' : '/api/v1/imports/attendance'
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { Authorization: `Bearer ${accessToken}` },
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json()
        message.error(error.detail || '上传失败')
        return
      }

      message.success('上传成功，正在处理中...')
      fetchBatches()
    } catch (error) {
      message.error('上传失败')
    }
  }

  const handleViewErrors = async (batchId: number) => {
    try {
      const response = await fetch(`/api/v1/imports/batches/${batchId}/errors`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })

      if (!response.ok) throw new Error('Failed to fetch')

      const data = await response.json()
      setErrors(data.items)
      setErrorModalOpen(true)
    } catch (error) {
      message.error('获取错误详情失败')
    }
  }

  const columns: TableColumnsType<ImportBatch> = [
    {
      title: '批次号',
      dataIndex: 'batch_no',
      key: 'batch_no',
      width: 180,
    },
    {
      title: '导入类型',
      dataIndex: 'import_type',
      key: 'import_type',
      width: 130,
      render: (text) => importTypeLabels[text] || text,
    },
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      ellipsis: true,
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
      title: '总行数',
      dataIndex: 'total_rows',
      key: 'total_rows',
      width: 80,
    },
    {
      title: '成功/失败',
      key: 'success_failed',
      width: 100,
      render: (_, record) => (
        <span>
          <Tag color="green">{record.success_rows}</Tag>
          <Tag color="red">{record.failed_rows}</Tag>
        </span>
      ),
    },
    {
      title: '导入时间',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 160,
      render: (text) => (text ? new Date(text).toLocaleString() : '-'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        record.failed_rows > 0 && (
          <Button type="link" icon={<EyeOutlined />} onClick={() => handleViewErrors(record.id)}>
            查看错误
          </Button>
        )
      ),
    },
  ]

  const errorColumns: TableColumnsType<ImportError> = [
    { title: '行号', dataIndex: 'row_no', key: 'row_no', width: 80 },
    { title: '错误代码', dataIndex: 'error_code', key: 'error_code', width: 120 },
    { title: '错误信息', dataIndex: 'error_message', key: 'error_message', ellipsis: true },
  ]

  if (!isAdmin) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h2>数据导入</h2>
        </div>
        <p>您没有权限访问此页面</p>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>数据导入</h2>
      </div>

      <div className={styles.filters}>
        <Space>
          <Upload
            accept=".xlsx,.xls,.csv"
            showUploadList={false}
            beforeUpload={(file) => {
              handleUpload(file, 'course_purchase')
              return false
            }}
          >
            <Button icon={<UploadOutlined />}>导入课程购买记录</Button>
          </Upload>
          <Upload
            accept=".xlsx,.xls,.csv"
            showUploadList={false}
            beforeUpload={(file) => {
              handleUpload(file, 'course_attendance')
              return false
            }}
          >
            <Button icon={<UploadOutlined />}>导入上课记录</Button>
          </Upload>
          <Select
            placeholder="筛选类型"
            value={importTypeFilter}
            onChange={setImportTypeFilter}
            allowClear
            style={{ width: 150 }}
            options={Object.entries(importTypeLabels).map(([value, label]) => ({ value, label }))}
          />
        </Space>
      </div>

      <div className={styles.tableContainer}>
        <Table
          columns={columns}
          dataSource={batches}
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
        title={`导入错误详情 - ${selectedBatch?.batch_no}`}
        open={errorModalOpen}
        onCancel={() => setErrorModalOpen(false)}
        footer={null}
        width={800}
      >
        <Table
          columns={errorColumns}
          dataSource={errors}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Modal>
    </div>
  )
}
