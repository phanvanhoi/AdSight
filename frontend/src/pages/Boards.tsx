import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, FolderOpen } from 'lucide-react'
import { listBoards, createBoard, deleteBoard, getBoardAds } from '../api/boards'
import AdGrid from '../components/search/AdGrid'
import LoadingSpinner from '../components/LoadingSpinner'
import type { Board } from '../types/board'

export default function Boards() {
  const queryClient = useQueryClient()
  const [selectedBoard, setSelectedBoard] = useState<Board | null>(null)
  const [newBoardName, setNewBoardName] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const { data: boards = [], isLoading: boardsLoading } = useQuery({
    queryKey: ['boards'],
    queryFn: listBoards,
  })

  const { data: boardAds, isLoading: adsLoading } = useQuery({
    queryKey: ['board-ads', selectedBoard?.id],
    queryFn: () => getBoardAds(selectedBoard!.id),
    enabled: !!selectedBoard,
  })

  const createMutation = useMutation({
    mutationFn: () => createBoard(newBoardName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['boards'] })
      setNewBoardName('')
      setShowCreate(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteBoard(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['boards'] })
      setSelectedBoard(null)
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Boards</h1>
          <p className="text-sm text-gray-500 mt-1">Luu va to chuc ads yeu thich</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700"
        >
          <Plus size={16} />
          Tao board
        </button>
      </div>

      {/* Create board form */}
      {showCreate && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 flex gap-3">
          <input
            type="text"
            value={newBoardName}
            onChange={(e) => setNewBoardName(e.target.value)}
            placeholder="Ten board..."
            className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm"
          />
          <button
            onClick={() => createMutation.mutate()}
            disabled={!newBoardName.trim()}
            className="px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            Tao
          </button>
        </div>
      )}

      {boardsLoading && <LoadingSpinner text="Dang tai boards..." />}

      <div className="flex gap-6">
        {/* Board list */}
        <div className="w-64 flex-shrink-0 space-y-2">
          {boards.map((board) => (
            <div
              key={board.id}
              className={`flex items-center justify-between p-3 rounded-lg cursor-pointer ${
                selectedBoard?.id === board.id
                  ? 'bg-primary-50 border border-primary-200'
                  : 'bg-white border border-gray-200 hover:bg-gray-50'
              }`}
              onClick={() => setSelectedBoard(board)}
            >
              <div className="flex items-center gap-2">
                <FolderOpen size={16} className="text-gray-400" />
                <span className="text-sm font-medium text-gray-700">{board.name}</span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  deleteMutation.mutate(board.id)
                }}
                className="p-1 text-gray-400 hover:text-red-500"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}

          {boards.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-8">Chua co board nao</p>
          )}
        </div>

        {/* Board content */}
        <div className="flex-1">
          {selectedBoard ? (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">{selectedBoard.name}</h2>
              <AdGrid
                ads={(boardAds?.results || []).map((ad: any) => ({ ...ad, days_running: 0 }))}
                loading={adsLoading}
              />
            </div>
          ) : (
            <div className="text-center py-16 text-gray-400">
              <FolderOpen size={48} className="mx-auto mb-3" />
              <p>Chon 1 board de xem ads da luu</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
