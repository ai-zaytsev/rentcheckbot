from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from db import models

AsyncSessionLocal = sessionmaker(bind=models.async_engine, class_=AsyncSession, expire_on_commit=False)

async def add_user_if_not_exists(id_user):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            user = await session.get(models.User, id_user)
            if not user:
                new_user = models.User(id=id_user)
                session.add(new_user)
                await session.commit()

async def add_address(text, id_user):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            address = models.Address(text=text, id_user=id_user)
            session.add(address)
            await session.commit()

async def address_exists(input_address):
    async with AsyncSessionLocal() as session:
        stmt = select(models.Address).where(models.Address.text == input_address)
        result = await session.execute(stmt)
        address = result.scalars().first()
        return address is not None

async def get_address_and_all_apartments(input_address):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(models.Address, models.Apartment)
            .join(models.Apartment, models.Address.id == models.Apartment.address_id)
            .where(models.Address.text == input_address)
        )
        result = await session.execute(stmt)
        address_apartments = result.all()
        if not address_apartments:
            return ""
        return "\n".join(f"{address.text} {apartment.apartment_num}" for address, apartment in address_apartments)
    
async def get_address_id(input_address):
    async with AsyncSessionLocal() as session:
        stmt = select(models.Address).where(models.Address.text == input_address)
        result = await session.execute(stmt)
        address = result.scalars().first()
        return address.id if address else None

async def add_apartment_to_address(apartment_num, address_id):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = select(models.Apartment).where(
                models.Apartment.apartment_num == apartment_num.upper(),
                models.Apartment.address_id == address_id
            )
            result = await session.execute(stmt)
            existing_apartment = result.scalars().first()
            if existing_apartment:
                return False  
            new_apartment = models.Apartment(apartment_num=apartment_num.upper(), address_id=address_id)
            session.add(new_apartment)
            await session.commit()
            return True

async def set_no_apartments(address_id):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            apartment_num = "No apartments in this building"
            stmt = select(models.Apartment).where(
                models.Apartment.apartment_num == apartment_num,
                models.Apartment.address_id == address_id
            )
            result = await session.execute(stmt)
            existing_apartment = result.scalars().first()        
            if existing_apartment:
                return False  
            new_apartment = models.Apartment(apartment_num=apartment_num, address_id=address_id)
            session.add(new_apartment)
            await session.commit()
            return True

async def delete_apartment(text: str, apartment_num: str) -> bool | None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Find the address with the given text
            addr_query = await session.execute(select(models.Address).filter(models.Address.text == text))
            address = addr_query.scalars().first()
            
            if address:
                # Find the apartment with the given number at the found address
                apt_query = await session.execute(select(models.Apartment).filter(models.Apartment.address_id == address.id,
                                                                           models.Apartment.apartment_num == apartment_num))
                apartment = apt_query.scalars().first()
                
                if apartment:
                    # Delete the found apartment
                    await session.delete(apartment)
                    
                    # Check if the address has other apartments
                    remaining_apts_query = await session.execute(select(models.Apartment).filter(models.Apartment.address_id == address.id))
                    remaining_apartments = remaining_apts_query.scalars().all()
                    
                    if not remaining_apartments:
                        # If no other apartments, delete the address
                        await session.delete(address)
                        
                    await session.commit()
                    return None
                else:
                    # No apartment found with the provided number at the specified address
                    return False
            else:
                # Address not found
                return False
