package com.akcrba.smartstep.lib.core.di

import android.content.Context
import androidx.room3.Room
import com.akcrba.smartstep.feature.myprofile.data.local.SmartStepDatabase
import com.akcrba.smartstep.feature.myprofile.data.local.dao.UserDao
import org.koin.core.annotation.Configuration
import org.koin.core.annotation.Module
import org.koin.core.annotation.Singleton

@Module
@Configuration
internal class DatabaseModule {

    @Singleton
    fun provideRoomDatabase(context: Context): SmartStepDatabase = Room.databaseBuilder(
        context,
        SmartStepDatabase::class.java,
        "smartstep_database",
    ).build()

    @Singleton
    fun provideUserDao(database: SmartStepDatabase): UserDao = database.userDao
}
