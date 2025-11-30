import express from 'express'
import payload from 'payload'
import dotenv from 'dotenv'

dotenv.config()

const app = express()
const PORT = process.env.PORT || 3001

// Initialize Payload
const start = async () => {
  await payload.init({
    secret: process.env.PAYLOAD_SECRET || 'your-secret-key-change-me',
    express: app,
    onInit: () => {
      payload.logger.info(`Payload Admin URL: ${payload.getAdminURL()}`)
    },
  })

  // Health check endpoint
  app.get('/health', (req, res) => {
    res.status(200).json({ status: 'healthy', service: 'payload-cms' })
  })

  app.listen(PORT, () => {
    payload.logger.info(`Server listening on port ${PORT}`)
  })
}

start()
