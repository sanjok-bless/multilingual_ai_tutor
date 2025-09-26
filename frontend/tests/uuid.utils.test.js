import { describe, it, expect, vi } from 'vitest'
import { generateUUID } from '@/utils/uuid.js'

describe('UUID Utils', () => {
  describe('generateUUID', () => {
    it('should generate valid UUID v4 format', () => {
      const uuid = generateUUID()

      // UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
      const uuidRegex =
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
      expect(uuid).toMatch(uuidRegex)
    })

    it('should generate unique UUIDs', () => {
      const uuid1 = generateUUID()
      const uuid2 = generateUUID()

      expect(uuid1).not.toBe(uuid2)
      expect(uuid1).toHaveLength(36)
      expect(uuid2).toHaveLength(36)
    })

    it('should generate consistent format with Math.random fallback', () => {
      const mathRandomSpy = vi.spyOn(Math, 'random').mockReturnValue(0.5)

      const uuid = generateUUID()

      expect(uuid).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
      )

      mathRandomSpy.mockRestore()
    })
  })
})
