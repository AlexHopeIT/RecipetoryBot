from aiogram import Router, types
from aiogram.client.bot import Bot
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from db import SessionLocal, Recipe, User, ShoppingList
from .states import FindRecipeState, ByIngredientsState
from utils import (send_random_recipe, start_search_dialog,
                   process_search_query_and_display_results,
                   send_selected_recipe_by_choice,
                   start_by_ingredients_search,
                   process_search_by_ingredients, from_favorites,
                   send_one_recipe)
from keyboards.inline import (
    main_menu_keyboard, recipe_actions_keyboard,
    favorites_paginated_keyboard,
    shopping_list_actions_keyboard
    )


user_handlers_router = Router()


@user_handlers_router.message(Command('random_recipe'))
async def random_recipe(message: types.Message,
                        state: FSMContext):
    '''Ручка для выдачи рандомного рецепта пользователю'''
    send_random_recipe(message, state)


@user_handlers_router.callback_query(
        lambda c: c.data == 'random_recipe_inline'
        )
async def random_recipe_inline(callback: types.CallbackQuery,
                               state: FSMContext):
    await callback.answer()
    await send_random_recipe(callback.message, state)


@user_handlers_router.message(Command('find_recipe'))
async def find_recipe(message: types.Message, state: FSMContext):
    '''Ручка для поиска рецепта по названию'''
    await start_search_dialog(message, state)


@user_handlers_router.callback_query(
        lambda c: c.data == 'find_recipe_inline'
        )
async def find_recipe_inline(callback: types.CallbackQuery,
                             state: FSMContext):
    await callback.answer()
    await start_search_dialog(callback.message, state)


@user_handlers_router.message(FindRecipeState.waiting_for_name)
async def process_recipe_name(message: types.Message, state: FSMContext):
    '''Первый шаг поиска. Подготовка списка найденных рецептов'''
    await process_search_query_and_display_results(message, state)


@user_handlers_router.message(FindRecipeState.waiting_for_choice)
async def process_recipe_choice(message: types.Message, state: FSMContext):
    '''Второй шаг поиска. Обработка выбора юзера'''
    await send_selected_recipe_by_choice(message, state)


@user_handlers_router.message(Command('by_ingredients'))
async def find_recipe_by_ingredients(message: types.Message, state: FSMContext):
    '''Ручка поиска по ингредиентам'''
    await start_by_ingredients_search(message, state)


@user_handlers_router.callback_query(
        lambda c: c.data == 'by_ingredients_inline'
        )
async def find_recipe_by_ingredients_inline(
    callback: types.CallbackQuery,
    state: FSMContext
):
    await callback.answer()
    await start_by_ingredients_search(callback.message, state)


@user_handlers_router.message(ByIngredientsState.waiting_for_ingredients)
async def process_recipe_ingredients(message: types.Message, state: FSMContext):
    '''Первый шаг поиска. Подготовка списка найденных рецептов'''
    await process_search_by_ingredients(message, state)


@user_handlers_router.message(ByIngredientsState.waiting_for_choice)
async def process_choice(message: types.Message, state: FSMContext):
    '''Второй шаг поиска. Обработка выбора юзера'''
    await send_selected_recipe_by_choice(message, state)


@user_handlers_router.callback_query(
    lambda c: c.data == 'main_menu_inline'
)
async def main_menu_inline(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    keyboard = await main_menu_keyboard(state)
    await callback.message.answer(
        'Вы вернулись в главное меню. Выберите действие:',
        reply_markup=keyboard
        )


@user_handlers_router.callback_query(
    lambda c: c.data == 'favorites_inline'
)
async def favorites_inline(callback: types.CallbackQuery, state: FSMContext):
    await from_favorites(callback, state)


@user_handlers_router.callback_query(
    lambda c: c.data.startswith('add_favorite:')
)
async def add_favorite(
    callback: types.CallbackQuery,
    state: FSMContext,
    bot: Bot
):
    await callback.answer()

    user_id = callback.from_user.id

    try:
        recipe_id = int(callback.data.split(':')[1])
    except (IndexError, ValueError):
        await callback.message.edit_text('Произошла ошибка с данными.')
        return

    async with SessionLocal() as db:
        user_result = await db.execute(
            select(User).options(
                selectinload(User.favorites_recipes)
            ).where(User.id == user_id)
        )
        recipe_result = await db.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )

        user = user_result.scalars().first()
        recipe = recipe_result.scalars().first()

        if user and recipe:
            if recipe in user.favorites_recipes:
                # Рецепт уже в избранном, просто обновляем кнопку
                await bot.edit_message_reply_markup(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    reply_markup=recipe_actions_keyboard(
                        is_favorite=True,
                        recipe_id=recipe_id
                    )
                )
                await callback.answer('Этот рецепт уже в избранном.')
                return

            try:
                user.favorites_recipes.append(recipe)
                await db.commit()
                await bot.edit_message_reply_markup(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    reply_markup=recipe_actions_keyboard(
                        is_favorite=True,
                        recipe_id=recipe_id
                    )
                )
                await callback.answer('Рецепт успешно добавлен в избранное.')
            except IntegrityError:
                await db.rollback() # Откатываем транзакцию при ошибке
                await callback.answer('Этот рецепт уже в избранном.')
            except Exception as e:
                await db.rollback() # Откатываем любую другую ошибку
                await callback.answer(f'Произошла неизвестная ошибка: {e}')


@user_handlers_router.callback_query(
    lambda c: c.data.startswith('remove_favorite:')
)
async def remove_favorite(
    callback: types.CallbackQuery,
    state: FSMContext,
    bot: Bot
                        ):
    print("Received callback data:", callback.data)  # Отладочная печать
    try:
        parts = callback.data.split(':')
        recipe_id = int(parts[1])
    except (IndexError, ValueError):
        return

    async with SessionLocal() as db:
        user_result = await db.execute(
            select(User)
            .options(selectinload(User.favorites_recipes))
            .where(User.id == callback.from_user.id)
        )
        user = user_result.scalars().first()

        recipe_result = await db.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )
        recipe = recipe_result.scalars().first()

        if user and recipe and recipe in user.favorites_recipes:
            user.favorites_recipes.remove(recipe)
            await db.commit()

            await db.refresh(user)
            updated_recipes = user.favorites_recipes

            if updated_recipes:
                keyboard = await favorites_paginated_keyboard(
                    updated_recipes, page=0
                    )
                await callback.message.edit_text(
                    '⭐️ Ваши избранные рецепты:\n'
                    'Выберите, чтобы посмотреть:',
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    'У вас больше нет избранных рецептов 🤷‍♂️',
                    reply_markup=await main_menu_keyboard(state)
                )
        else:
            await callback.message.answer(
                'Этот рецепт уже не в вашем избранном.'
            )


@user_handlers_router.callback_query(
    lambda c: c.data.startswith('back_to_recipe')
)
async def back_to_recipe(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    try:
        recipe_id = int(callback.data.split(':')[1])
    except (IndexError, ValueError):
        keyboard = await main_menu_keyboard(state)
        await callback.message.answer(
            'Ошибка при получении ID рецепта... Возвращаю в главное меню',
            reply_markup=keyboard
        )
        return

    async with SessionLocal() as db:
        result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
        found_recipe = result.scalars().first()

        if found_recipe:
            user_id = callback.from_user.id
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalars().first()
            is_favorite = found_recipe in user.favorites_recipes if user else False

            await send_one_recipe(
                callback.message, found_recipe, is_favorite, state
            )

            await state.clear()
        else:
            keyboard = await main_menu_keyboard(state)

            await callback.message.answer(
                'Произошла внутренняя ошибка...\n'
                'Возвращаю в главное меню...',
                reply_markup=keyboard
            )


@user_handlers_router.callback_query(
        lambda c: c.data.startswith('view_recipe:')
        )
async def view_recipe(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    try:
        parts = callback.data.split(':')
        recipe_id = int(parts[1])
        page_from_list = int(parts[2])
    except (IndexError, ValueError):
        return

    async with SessionLocal() as db:
        recipe_result = await db.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )
        found_recipe = recipe_result.scalars().first()

        user_result = await db.execute(
            select(User)
            .options(selectinload(User.favorites_recipes))
            .where(User.id == callback.from_user.id)
        )
        user = user_result.scalars().first()
        is_favorite = found_recipe in user.favorites_recipes if user and found_recipe else False

        if found_recipe:
            await send_one_recipe(
                callback.message,
                found_recipe,
                is_favorite,
                state,
                page=page_from_list
            )

            await state.clear()
        else:
            await callback.message.answer(
                'К сожалению, рецепт не найден.'
            )


@user_handlers_router.callback_query(
        lambda c: c.data.startswith('favorites_page:')
        )
async def favorites_page_handler(
    callback: types.CallbackQuery, state: FSMContext
                ):
    await callback.answer()

    try:
        page = int(callback.data.split(':')[1])
    except (IndexError, ValueError):
        keyboard = await main_menu_keyboard(state)
        await callback.message.answer(
            'Произошла ошибка, возвращаюсь в главное меню.',
            reply_markup=keyboard
        )
        return

    async with SessionLocal() as db:
        user_result = await db.execute(
            select(User).options(selectinload(User.favorites_recipes))
            .where(User.id == callback.from_user.id)
        )
        user = user_result.scalars().first()

    if user and user.favorites_recipes:
        keyboard = await favorites_paginated_keyboard(
            user.favorites_recipes,
            page=page
        )

        await callback.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=keyboard
        )
    else:
        # Если список избранного внезапно стал пустым
        keyboard = await main_menu_keyboard(state)
        await callback.message.answer(
            'У вас больше нет избранных рецептов 🤷‍♂️',
            reply_markup=keyboard
        )


@user_handlers_router.callback_query(
        lambda c: c.data.startswith('add_to_shopping_list')
        )
async def add_to_shopping_list_handler(
    callback: types.CallbackQuery, state: FSMContext
                ):
    await callback.answer('Ингредиенты добавлены в список покупок')

    user_id = callback.from_user.id
    try:
        recipe_id = int(callback.data.split(':')[1])
    except (IndexError, ValueError):
        await callback.message.edit_text(
            'Произошла ошибка с данными... Попробуйте ещё раз'
        )
        return

    async with SessionLocal() as db:
        recipe_result = await db.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )
        found_recipe = recipe_result.scalars().first()

        if found_recipe:
            ingredients_text = found_recipe.ingredients_ru
            ingredients_list = [
                item.strip() for item in ingredients_text.split('\n') if item.strip()
            ]

            for item in ingredients_list:
                new_item = ShoppingList(user_id=user_id, item_name=item)
                db.add(new_item)
            await db.commit()

            await callback.message.answer(
                'Список покупок обновлен!',
                reply_markup=await main_menu_keyboard(state)
            )
        else:
            callback.message.answer(
                'Сожалею, но рецепт не найден...'
            )


@user_handlers_router.callback_query(
        lambda c: c.data.startswith('view_shopping_list')
        )
async def view_shopping_list_handler(
    callback: types.CallbackQuery, state: FSMContext
                ):
    await callback.answer()

    user_id = callback.from_user.id

    async with SessionLocal() as db:
        shopping_list_result = await db.execute(
            select(ShoppingList).where(
                ShoppingList.user_id == user_id
            )
        )
        shopping_items = shopping_list_result.scalars().all()

        if not shopping_items:
            await callback.message.edit_text(
                'Ваш список покупок пуст. Добавьте в него'
                ' ингредиенты из избранных рецептов',
                reply_markup=await main_menu_keyboard(state)
            )
            return

        items_text = '\n'.join([
            f'~~{item.item_name}~~' if item.is_purchased else f'• {item.item_name}' 
            for item in shopping_items
        ])
        try:
            await callback.message.edit_text(
                f'<b>🛒 Ваш список покупок</b>:\n'
                'Купленные ингредиенты отмечайте кнопкой ☑️ '
                '(для отмены нажмите на ингредиент еще раз)\n'
                'Чтобы удалить ингредиент из списка (безвозвратно!), нажмите ❌\n\n'
                f'{items_text}\n\n'
                'Чтобы удалить весь список, нажмите кнопку ниже.',
                reply_markup=await shopping_list_actions_keyboard(
                    shopping_items
                    ),
                parse_mode='HTML'
            )
        except Exception as e:
            await callback.message.answer(
                f'Произошла ошибка при обновлении списка: {e}'
            )


@user_handlers_router.callback_query(
    lambda c: c.data.startswith('clear_shopping_list')
    )
async def clear_shopping_list_handler(
    callback: types.CallbackQuery, state: FSMContext
                ):
    await callback.answer('Список покупок очищен полностью!')

    user_id = callback.from_user.id

    async with SessionLocal() as db:
        await db.execute(
            delete(ShoppingList).where(ShoppingList.user_id == user_id)
        )
        await db.commit()

        await callback.message.edit_text(
            'Ваш список покупок полностью очищен! ✅',
            reply_markup=await main_menu_keyboard(state)
        )


@user_handlers_router.callback_query(
    lambda c: c.data.startswith('toggle_purchased:')
    )
async def toggle_purchased_item(
    callback: types.CallbackQuery, state: FSMContext
        ):
    item_id = int(callback.data.split(':')[1])

    async with SessionLocal() as db:
        item = await db.get(ShoppingList, item_id)
        if item:
            item.is_purchased = not item.is_purchased
            await db.commit()

    await view_shopping_list_handler(callback, state)


@user_handlers_router.callback_query(
    lambda c: c.data.startswith('delete_item:')
)
async def delete_shopping_list_item(callback: types.CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split(':')[1])

    async with SessionLocal() as db:
        await db.execute(
            delete(ShoppingList).where(ShoppingList.id == item_id)
        )
        await db.commit()

    await view_shopping_list_handler(callback, state)
