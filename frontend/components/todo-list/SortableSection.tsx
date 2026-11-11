import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type Announcements,
  type DragEndEvent,
} from "@dnd-kit/core";
import { restrictToParentElement, restrictToVerticalAxis } from "@dnd-kit/modifiers";
import { SortableContext, arrayMove, sortableKeyboardCoordinates, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { Todo, TodoPatch } from "@/api/client";
import { TodoRow } from "./TodoRow";

export type RowHandlers = {
  onUpdate: (id: number, patch: TodoPatch) => void;
  onRemove: (id: number) => void;
  onReorder: (ids: number[]) => void;
};

/** A drag-sortable list. Items can only be dragged within their own section. */
export function SortableSection({ todos, onReorder, ...handlers }: { todos: Todo[] } & RowHandlers) {
  const sensors = useSensors(
    // A small distance threshold keeps plain clicks on the handle from starting a drag.
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const textOf = (id: unknown) => `"${todos.find(t => t.id === id)?.text ?? "item"}"`;
  const position = (id: unknown) => `${todos.findIndex(t => t.id === id) + 1} of ${todos.length}`;
  const announcements: Announcements = {
    onDragStart: ({ active }) => `Picked up ${textOf(active.id)}, position ${position(active.id)}.`,
    onDragOver: ({ active, over }) => (over ? `${textOf(active.id)} is over position ${position(over.id)}.` : undefined),
    onDragEnd: ({ active, over }) =>
      over ? `Dropped ${textOf(active.id)} at position ${position(over.id)}.` : `Dropped ${textOf(active.id)}.`,
    onDragCancel: ({ active }) => `Cancelled moving ${textOf(active.id)}.`,
  };

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    if (!over || active.id === over.id) return;
    const from = todos.findIndex(t => t.id === active.id);
    const to = todos.findIndex(t => t.id === over.id);
    if (from < 0 || to < 0) return;
    onReorder(arrayMove(todos, from, to).map(t => t.id));
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      modifiers={[restrictToVerticalAxis, restrictToParentElement]}
      onDragEnd={onDragEnd}
      accessibility={{
        announcements,
        screenReaderInstructions: {
          draggable: "To reorder, press space or enter, use the arrow keys to move, then press space or enter again to drop. Press escape to cancel.",
        },
      }}
    >
      <SortableContext items={todos.map(t => t.id)} strategy={verticalListSortingStrategy}>
        <ul className="flex flex-col">
          {todos.map(todo => (
            <TodoRow key={todo.id} todo={todo} {...handlers} />
          ))}
        </ul>
      </SortableContext>
    </DndContext>
  );
}
